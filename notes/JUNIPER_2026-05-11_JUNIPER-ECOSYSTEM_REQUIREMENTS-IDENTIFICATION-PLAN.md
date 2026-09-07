# Requirements Identification Plan

**Author**: Paul Calnon
**Created**: 2026-05-11
**Last updated**: 2026-05-11
**Status**: Plan locked. Execution not yet started.
**Owner**: Paul Calnon (work to be performed by Claude Code agents under supervision)

**Operator surface (v5 consolidator):** [`docs/REFERENCE.md` § Requirements Snapshot Consolidation](../docs/REFERENCE.md#requirements-snapshot-consolidation) — `by-area` is the corpus of record; the ledger has no `detail`.

---

## 1. Goal

Search every notes document across all 8 active Juniper repositories, extract every explicit and (under an aggressive threshold) implicit project / application-level requirement, and consolidate them into a single navigable set of markdown files in `juniper-ml/notes/requirements/` with a top-level index at `juniper-ml/notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`.

The output is a **historically-accurate snapshot** of the full requirements picture as of the execution date. Already-shipped requirements are included with `status: shipped`. Each requirement entry must trace back to at least one cited source-document path with line range; hallucinated requirements are the primary risk and the schema enforces traceability.

This is a **v1 snapshot**. Iteration toward a "living document" model is documented as future work in §10.

---

## 2. Scope

### In scope (v1)

- All files under `notes/` in each of the 8 active repos:
  - `juniper-cascor/notes/`
  - `juniper-data/notes/`
  - `juniper-data-client/notes/`
  - `juniper-cascor-client/notes/`
  - `juniper-cascor-worker/notes/`
  - `juniper-canopy/notes/`
  - `juniper-deploy/notes/`
  - `juniper-ml/notes/`
- Both **explicit** requirements (anything formally tagged: "Requirement", "Acceptance Criteria", "Must", "Shall", numbered req lists, structured checklists in plan docs) and **implicit** requirements under an **aggressive** threshold — see §4 for the explicit definition of what aggressive includes.
- Both **open** and **shipped** requirements. The list is intended to capture the full historical picture.

### Out of scope for v1 (deferred to future work — see §10)

- PR descriptions, issue text, GitHub discussions
- Design docs in `docs/` directories
- Code-level docstrings
- Conversation-derived requirements (Slack, email, in-person)
- Living-document refresh mechanisms (CI lint, scheduled re-extraction, author-side tagging conventions)

---

## 3. Locked decisions (questions and answers)

The plan was reviewed and these five questions were resolved 2026-05-11. Re-opening any of them requires a documented decision change here.

### Q1 — How aggressive should "implicit" requirement identification be?

**Question**: Should the extraction be aggressive (every "must/should/will" sentence + every TODO + every threshold/SLO/perf target) or conservative (only structured requirement-like blocks)?

**Answer (locked 2026-05-11)**: **Aggressive.** Capture as much as possible in v1. Noise can be filtered later via the `status` and `category` fields; missed items are harder to recover after the fact.

**Implication**: Phase-3 extraction agents are instructed to err on inclusion. Expect ~500-1000 candidate requirements across the 8 repos before deduplication. Dedup in Phase 4 collapses cross-repo restatements of the same requirement into single entries with multiple source references.

### Q2 — Single monolithic file or multi-file?

**Question**: One big `REQUIREMENTS.md` (~5000-15000 lines) or multi-file (per-repo / per-component / per-domain) with a navigation index?

**Answer (locked 2026-05-11)**: **Multi-file.** Output structure:

```bash
notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md             ← navigation entrypoint
notes/requirements/
├── README.md                           ← schema + ID convention reference
├── by-area/
│   ├── observability.md
│   ├── security.md
│   ├── api-contracts.md
│   ├── deployment.md
│   ├── ui-frontend.md
│   ├── data-pipeline.md
│   ├── training.md
│   ├── networking-and-comms.md
│   ├── testing-and-ci.md
│   └── ... (other areas as discovered)
├── by-repo/
│   ├── juniper-cascor.md               ← thin index of JR-CAS-* IDs grouped by area
│   ├── juniper-data.md                 ← JR-DAT-*
│   ├── juniper-canopy.md               ← JR-CAN-*
│   ├── juniper-deploy.md               ← JR-DEP-*
│   ├── juniper-ml.md                   ← JR-ML-*
│   ├── juniper-cascor-worker.md        ← JR-CWK-*
│   ├── juniper-cascor-client.md        ← JR-CCL-*
│   └── juniper-data-client.md          ← JR-DCL-*
└── by-status/
    ├── shipped.md                      ← thin index by status
    ├── in-progress.md
    ├── proposed.md
    ├── deferred.md
    └── ... (other statuses)
```

The **canonical** definition of each requirement lives once in `by-area/<area>.md`. The `by-repo/` and `by-status/` files are thin indexes that link into `by-area/` — not duplicates. This avoids the maintenance trap of three copies of every requirement going stale independently.

> **SUPERSEDED 2026-08-31 — what shipped is a generated projection, not a thin index.** The design
> above was never built as written: `by-repo/` and `by-status/` carry **full entry bodies**, and by
> 2026-08-26 the three families had begun to drift apart in 201 places (52 by-repo vs by-area, 149
> by-status vs by-area) — the exact trap this paragraph was written to prevent.
>
> **ml#1462 removed the trap by a different route.** `by-area` stays canonical and the other two
> families are **derived from it**: `FAMILIES_WRITTEN_BY_WRITE_ALL` is `by-area` alone, so exactly
> one writer owns each file, and `--check-views` fails when a derived family disagrees with its
> source. Three independent copies is what caused the drift; derivation eliminates that regardless
> of whether the copies are thin. Link-only would *also* have removed the trap, but at the cost of
> content readers use — which was never the point of the constraint.
>
> Keep the sentence above as the recorded intent; treat the projection as the shipped design. The
> owner decision that chose it is in
> [`JUNIPER_2026-08-26_JUNIPER-ECOSYSTEM_REQUIREMENTS-CROSS-VIEW-MEASUREMENT.md`](JUNIPER_2026-08-26_JUNIPER-ECOSYSTEM_REQUIREMENTS-CROSS-VIEW-MEASUREMENT.md).
>
> **A limit worth carrying with it:** `--check-views` compares the families against each other, so
> it can only find a defect they DISAGREE about. A defect every family shares — because all three
> are generated from one canonical entry — is invisible to it by construction. That is how 172
> malformed entry titles survived every view gate (ml#1475 §5; 81 repaired in ml#1511).

### Q3 — Snapshot or living document?

**Question**: Capture state as-of-today, or also wire a refresh path?

**Answer (locked 2026-05-11)**: **Snapshot first.** The eventual need for a living-document model is real and documented in §10 ("Living-document migration plan"). Don't try to do both in v1.

### Q4 — Sources beyond `notes/`?

**Question**: Stick to `notes/` only, or also pull from PR descriptions, design docs, code docstrings, GitHub issues?

**Answer (locked 2026-05-11)**: **`notes/` only for v1.** Explicit out-of-scope sources are listed in §10.2 with the reasoning for each — so anyone reading this doc later understands the boundary was deliberate, not accidental.

### Q5 — Already-shipped requirements: include or filter?

**Question**: Include with `status: shipped` or filter out?

**Answer (locked 2026-05-11)**: **Include with `status: shipped`.** The requirements documents are intended to represent the full, historically-accurate picture of the project. Hiding shipped work loses the audit trail and makes recurring ideas look like new ideas.

---

## 4. Definition of "aggressive implicit requirement identification" (per Q1)

For Phase 3 extraction agents, the following are all treated as candidate requirements:

| Pattern                                                                   | Example                                                                    | Treat as    | Status default                           |
|---------------------------------------------------------------------------|----------------------------------------------------------------------------|-------------|------------------------------------------|
| Explicit "Requirement N: …" or "REQ-N:" headings                          | "Requirement 4.2: cascor must expose /v1/health/ready"                     | requirement | based on context                         |
| Acceptance-criteria checklist items                                       | "- [x] /metrics returns 200 anonymously"                                   | requirement | inferred from checkbox state             |
| "Must / shall / should / will / cannot" sentences in a design or plan doc | "Canopy shall not log API keys"                                            | requirement | `proposed` unless context says otherwise |
| Numbered design-decision rationale                                        | "**Decision**: use IP-allowlist on /metrics"                               | requirement | `shipped` if cited PR is merged          |
| TODO items in a roadmap or plan                                           | "TODO: wire OBS-WIRE-02"                                                   | requirement | `proposed`                               |
| Performance / latency / throughput targets                                | "p95 < 50 ms", "must support 100 RPS"                                      | requirement | `proposed` unless tied to a shipped SLO  |
| SLO / SLI definitions                                                     | "Availability SLI: 99.5%"                                                  | requirement | `shipped` if catalogued                  |
| Naming/format conventions stated as expectations                          | "All Helm charts: version and appVersion must match"                       | requirement | `shipped` if practiced                   |
| Architectural constraints                                                 | "Worker must not import pydantic at runtime"                               | requirement | `shipped` if test exists                 |
| Trigger conditions in deferred-design docs                                | The Option C triggers in JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md | requirement | `deferred`                               |
| Compatibility / pin floors stated as deliberate                           | "juniper-observability >= 0.2.0 floor for register_or_reuse"               | requirement | `shipped`                                |

**Not** treated as requirements:

- Pure historical narrative ("we tried X, it failed, we did Y")
- Status reports / changelogs without a forward-looking ask
- Internal-to-Claude/agent process notes that have no project-level implication

When in doubt under the aggressive threshold, **include**. Deduplication and triage happen in Phase 4.

---

## 5. Per-requirement schema

Every requirement entry in `by-area/*.md` MUST include the following fields. The schema is enforced in Phase 5 QA.

```markdown
### JR-CAS-WS-014 — WebSocket resume buffer occupancy

**Status**: shipped <!-- one of: proposed | designed | in-progress | shipped | deferred | rejected | superseded -->
**Priority**: P1 <!-- one of: P0 | P1 | P2 | P3 ; see §5.1 for inference rules -->
**Category**: observability  <!-- canonical area; matches a by-area/ file -->
**Owner**: cascor  <!-- canonical owning repo -->
**Brief**: Cascor must expose current and capacity occupancy of the WS replay
buffer as Prometheus gauges so operators can detect resume-storm pressure.

**Sources**:
- juniper-ml/notes/observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md §3.2 (lines 84-118)
- juniper-cascor/notes/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md §4.1.4 (lines 312-340)

**Detail**: Two `Gauge` collectors named `cascor_ws_replay_buffer_occupancy`
and `cascor_ws_replay_buffer_capacity`. Updated at every replay-buffer mutation
and at one-shot init respectively. Single label set: none (process-wide).
Cardinality budget: 2 series total.

**Design**: Wire at `manager.py:317` (occupancy) and `manager.py:94` (capacity
init) using `juniper_observability.register_or_reuse`. Helper module already
exists; this requirement adds two specific call sites.

**PRs**:
- pcalnon/juniper-cascor#204 — initial wiring of two of nine WS metrics (does NOT include this one)
- OBS-WIRE-02 — proposed PR that would close this; not yet opened

**Notes**: Part of the A.9 audit. See companion JR-CAS-WS-015 ... 022 for the
sibling WS metrics. Removing the `cascor_ws_seq_gap_detected_total` and
`cascor_ws_connections_active` (endpoint label) metrics is tracked under
JR-CAS-WS-021 and JR-CAS-WS-022 respectively.
```

### Field rules

- **`Status`** — required, one of the values in §6.
- **`Priority`** — required, one of `P0` / `P1` / `P2` / `P3`. Inferred from source-doc language only; see §5.1 for the inference rules. Never derived from extractor judgment.
- **`Category`** — required, must be one of the 15 locked area codes in §6. Phase-3 agents may not invent new area codes; anything that doesn't fit goes under the closest match and gets re-bucketed in Phase 4.
- **`Owner`** — required, the canonical owning repo (e.g. `cascor`, `canopy`, `deploy`, `ml`). Cross-repo requirements have one owner; the others appear in `Sources`.
- **`Brief`** — required, 1-2 sentences. Reads as a standalone summary.
- **`Sources`** — required, at least one. Format: `<repo>/<path> §<section> (lines <range>)`. Hallucinated requirements without traceable sources are the main risk; the schema makes them obviously broken.
- **`Detail`** — required for non-trivial entries; may be `(none)` for one-line conventions.
- **`Design`** — optional but recommended; populated when the source doc has a design sketch.
- **`PRs`** — optional; populated when one or more PRs exist that close (or partially close) the requirement.
- **`Notes`** — optional; cross-references to sibling requirements, related deferrals, etc.

### 5.1 Priority inference rules (locked 2026-05-12)

The priority field was added in Phase 2 after the Phase-1 inventory implied >1500 candidate requirements (total density score 12,926 across 625 files; see §11 Phase-1 results). With this volume, navigation requires a priority filter on top of `status`.

**Taxonomy** (P0 highest urgency, P3 lowest):

| Level  | Inferred when source doc shows …                                                                                                                                                |
|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **P0** | Words like *blocker*, *critical*, *production incident*, *must-ship-before-X*; open incident remediation plans; security CVE/CVSS-high fixes; data-loss or correctness defects. |
| **P1** | Listed in a current-quarter roadmap, has an explicit owner + ETA, or is named in a release-preparation / pre-deploy roadmap with a near-term target.                            |
| **P2** | Backlog / future-quarter item; no concrete ETA; *should* / *planned* language without urgency cues.                                                                             |
| **P3** | *Nice to have*, *future work*, *deferred*, *out of scope for v1*, *parking lot*, or explicitly tagged for a much later milestone.                                               |

**Default**: If the source doc gives no cue, default to **P2** and mark the entry with `**Priority-inferred**: true` (extractor metadata; this becomes a Notes line, e.g. `Notes: Priority defaulted to P2 — no urgency cues in source.`).

**Hard rule**: Priority is derived *from source-doc language only*. Extractor agents must not apply independent judgment about what "should" be P0/P1/P2/P3; that would re-introduce hallucination risk through the back door.

---

## 6. ID convention and status taxonomy

### Reference IDs

Format: `JR-<REPO>-<AREA>-<NNN>`

- `JR` — Juniper Requirement (constant prefix)
- `<REPO>` — 3-letter shortcode for the owning repo:
  - `CAS` = juniper-cascor
  - `CAN` = juniper-canopy
  - `DAT` = juniper-data
  - `DEP` = juniper-deploy
  - `ML`  = juniper-ml
  - `CWK` = juniper-cascor-worker
  - `CCL` = juniper-cascor-client
  - `DCL` = juniper-data-client
- `<AREA>` — 2-5 letter area code from the **locked 15-code enum** (Phase 2, 2026-05-12). Phase-3 agents may NOT invent new area codes. New codes may be added only after Phase-4 consolidation, with a recorded decision row in §11.
- `<NNN>` — zero-padded sequential within the (repo, area) namespace, starting at 001

**Locked area-code enum (15 codes)**:

| Code    | Scope                                                                                    |
|---------|------------------------------------------------------------------------------------------|
| `OBS`   | observability — metrics, logging, tracing, dashboards, alerting                          |
| `SEC`   | security — authn, authz, secrets, CVEs, hardening                                        |
| `API`   | API contracts — schemas, versioning, compatibility, migrations                           |
| `DEP`   | deployment-config — Docker, Compose, K8s, Helm, image build                              |
| `UI`    | ui-frontend — Canopy/Dash, UX, visualizations                                            |
| `DATA`  | data-pipeline — dataset generation, NPZ contracts, ingestion                             |
| `TRAIN` | training — cascor algorithm, candidates, convergence, model state                        |
| `WS`    | websocket / messaging — Canopy↔Cascor streaming, replay, control plane                   |
| `TEST`  | testing-and-ci — pytest, fixtures, CI workflows, regression analysis                     |
| `LOCK`  | lockfile-and-deps — uv lockfiles, pyproject pins, dep updates, env rebuilds              |
| `ARCH`  | architecture / cross-cutting design — microservices, polyrepo, interface proposals       |
| `PERF`  | performance / scalability — throughput, latency, parallelization, CUDA                   |
| `TOOL`  | dev tooling / scripts / workflow — worktree procs, claude-code launchers, util/* scripts |
| `DOC`   | documentation / process — link validation, conventions, file headers, READMEs            |
| `OPS`   | operations / runbooks / on-call — runbook documents, incident response, day-2            |

Examples: `JR-CAS-WS-014`, `JR-CAN-OBS-007`, `JR-DEP-OPS-003`, `JR-ML-LOCK-002`, `JR-ML-ARCH-011`.

IDs are assigned in Phase 4 (after dedup), recorded in `id_assignments.yaml`, and **never reused** even if a requirement is later marked `rejected` or `superseded`. A `superseded` entry retains its ID and links forward to its replacement.

### Status taxonomy

| Status        | Meaning                                                                                                        |
|---------------|----------------------------------------------------------------------------------------------------------------|
| `proposed`    | Identified in a notes doc but no design or implementation work has begun.                                      |
| `designed`    | A design doc exists but no implementation work has begun.                                                      |
| `in-progress` | One or more PRs are open / in active development.                                                              |
| `shipped`     | Closed by one or more merged PRs; the requirement is satisfied in the current main branch of all owning repos. |
| `deferred`    | Explicitly deferred with conditions for future activation (e.g. trigger criteria documented).                  |
| `rejected`    | Explicitly decided against; retained for historical traceability.                                              |
| `superseded`  | Replaced by another requirement; the entry stays with a forward link to the replacement's ID.                  |

---

## 7. Phased execution plan

| Phase | Description                                                                               | Approx wall-clock                        | Status        |
|-------|-------------------------------------------------------------------------------------------|------------------------------------------|---------------|
| 0     | Plan written, decisions locked                                                            | done                                     | ✅ 2026-05-11 |
| 1     | Inventory all `notes/` directories across the 8 repos                                     | 15-30 min, 1 Explore agent               | ☐ not started |
| 2     | Schema lock (already drafted in §5; re-confirm after Phase 1 size estimate)               | 10 min, deterministic                    | ☐ not started |
| 3     | Per-repo extraction, parallel                                                             | 1-3 h wall, 8 Explore agents in parallel | ☐ not started |
| 4     | Consolidation, dedup, ID assignment, area-grouping                                        | 30-60 min, sequential                    | ☐ not started |
| 5     | QA pass: random N=20 verification + coverage spot-check                                   | 30 min, 1 Explore agent + supervisor     | ☐ not started |
| 6     | Ship: commit `notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md` + `notes/requirements/*.md` to juniper-ml main | 10 min                                   | ☐ not started |

**Pilot recommendation (still in force)**: run all phases against `juniper-ml/notes/` only first (~1 hour total), recalibrate the aggressive-threshold and schema based on what surfaces, then fan out Phase 3 to the other 7 repos. The pilot output is **disposable** — Phase 3 will re-extract `juniper-ml` from scratch in the full-fan-out run.

### Phase detail

#### Phase 1 — Inventory

- One Explore agent runs `find notes/ -type f \( -name '*.md' -o -name '*.txt' \)` across all 8 repos.
- For each file: capture path, LOC, last-modified date, first-line summary.
- Identify the ~10-20 most "requirement-dense" files (roadmaps, plan docs, design proposals) — these will dominate Phase 3 effort.
- Output: `/tmp/notes_inventory_2026-05-11.md` (single index file consumed by Phase 3 agents).

#### Phase 2 — Schema lock

- Re-confirm §5 schema after Phase 1 size estimate. If Phase 1 surfaces > 1500 candidate requirements, may add a `priority` field; otherwise leave schema as-is.
- Pin the area-code list (the `<AREA>` part of the ID convention). Phase 3 agents must NOT invent new area codes; they pick from the pinned list or use `MISC` and let Phase 4 reclassify.

#### Phase 3 — Per-repo extraction (parallel)

- One Explore agent per repo (8 agents). Each agent gets:
  - The full schema from §5
  - The aggressive-threshold definition from §4
  - The pinned area-code list from Phase 2
  - The Phase-1 inventory entries for its repo
- Output per agent: a YAML file at `/tmp/req_extract_<repo>_2026-05-11.yaml`. Each entry contains all schema fields **except** the final ID (assigned in Phase 4 after dedup).
- Hard rule: every entry MUST cite at least one source-doc path with line range. Entries failing this rule are dropped in Phase 4 dedup.

#### Phase 4 — Consolidation

- Merge the 8 YAML files.
- Dedup pass: cross-repo restatements of the same requirement collapse to a single entry with multiple `Sources`. Heuristic: same `Brief` (after fuzzy match) + same `Category` + overlapping language → merge candidate, surface for human review.
- ID assignment: walk the merged set in deterministic order (alphabetic by Brief), assign `JR-<REPO>-<AREA>-<NNN>` IDs, persist to `id_assignments.yaml`.
- Generate the markdown:
  - `notes/requirements/by-area/*.md` (canonical entries)
  - `notes/requirements/by-repo/*.md` (thin indexes linking to by-area)
  - `notes/requirements/by-status/*.md` (thin indexes linking to by-area)
  - `notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md` (navigation entrypoint with stats)
- Validate: every `Source` path resolves on disk; every PR reference resolves on GitHub.

#### Phase 5 — QA

- Pick N=20 requirements at random. One Explore agent re-verifies each against its cited source doc, confirming:
  - The requirement is actually stated in the source (not invented)
  - The `Brief` faithfully summarises the source
  - The `Status` matches what the source/PR state says
- Coverage check: pick 5 notes files that should have produced requirements but appear in few/no `Sources`. Re-extract just those with a fresh agent. Surface anything missed.
- Findings → either iterate Phase 3-4 partial re-runs, or accept and ship.

#### Phase 6 — Ship

- Commit to the cached-whistling-flute worktree.
- Push branch to origin.
- Stash any in-progress edits in juniper-ml main worktree (recurring pattern this session — see relevant memory entries).
- Local-merge to main with `--no-ff`, push main.
- Restore the stash.
- Update §11 progress tracker with completion timestamp.

---

## 8. Risks and mitigations

| Risk                                                                   | Likelihood                                   | Impact                                     | Mitigation                                                                                                                                                                    |
|:-----------------------------------------------------------------------|:---------------------------------------------|:-------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Hallucinated requirements (extracted but no traceable source)          | medium                                       | high (corrupts the artifact's audit value) | Schema mandates at least one `Source` with line range. Phase 5 QA sample of N=20 catches a meaningful fraction.                                                               |
| ID collisions / shifting IDs on re-runs                                | medium                                       | medium (breaks external links)             | Persist `id_assignments.yaml`. Future re-runs reuse IDs for matched entries. Never reuse a retired ID.                                                                        |
| Aggressive threshold produces overwhelming volume (>1500 entries)      | medium                                       | medium (output unreviewable)               | Phase 1 inventory sizes the corpus before Phase 3 commits. If Phase 1 forecasts > 1500 entries, Phase 2 adds a `priority` field and Phase 4 surfaces a `priority: high` view. |
| Cross-repo restatements miss dedup (same requirement, two entries)     | high                                         | low (cosmetic; can be re-merged later)     | Phase 4 fuzzy-match dedup with human review of the merge candidates.                                                                                                          |
| Aggressive scope misses an explicit requirement (false negative)       | low-medium                                   | medium                                     | Phase 5 coverage check on 5 high-density files catches obvious misses.                                                                                                        |
| In-progress edits in main worktree get clobbered during Phase 6 commit | medium (already happened twice this session) | low (stash recovers)                       | Standard stash + merge + pop pattern, documented in `project_juniper_ml_concurrent_session_activity.md`.                                                                      |
| Phase 3 agent token cost exceeds expectations                          | medium                                       | low                                        | Run pilot on juniper-ml first (~1 hour, single-repo cost); use that to project full-fan-out cost before committing.                                                           |

---

## 9. Effort estimate

| Phase                                  | Wall-clock       | Notes                                                           |
|----------------------------------------|------------------|-----------------------------------------------------------------|
| 1 — Inventory                          | 15-30 min        | Mostly `find` + `wc` operations, single agent.                  |
| 2 — Schema lock                        | 10 min           | Deterministic, mostly already done in §5.                       |
| 3 — Extraction (full fan-out)          | 1-3 hours wall   | 8 agents in parallel. Token cost is the dominant resource here. |
| 3 — Extraction (juniper-ml pilot only) | ~1 hour          | Single agent against the densest repo.                          |
| 4 — Consolidation                      | 30-60 min        | Sequential, agent-assisted but supervisor-driven.               |
| 5 — QA                                 | 30 min           | One agent + spot-check.                                         |
| 6 — Ship                               | 10 min           | Standard commit-push-merge flow.                                |
| **Total (pilot only)**                 | **~2-2.5 hours** | Recommended starting point.                                     |
| **Total (full fan-out)**               | **~3-5 hours**   | After pilot validates the approach.                             |

---

## 10. Future work (deferred, with rationale)

Per Q3 (snapshot first) and Q4 (notes/ only for v1), the following are explicitly deferred. Each entry includes the conditions under which it should be promoted to active work.

> **2026-05-16 status update (post-v4 ship)**: The forward-looking work captured in this section has now been refined and expanded with v1-v4 empirical experience. The actionable, current version of the forward plan lives in [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md`](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md). The subsections below are retained for historical context (they capture v1-era thinking that informed but does not replace the new doc).

### 10.1 Living-document refresh

**v4 status**: Decomposed into 4 separate initiatives in `JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md`: [§4 PR refs](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#4-jr-id-references-in-prs), [§5 author-side tagging](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#5-author-side-jr-id-tagging-in-notes), [§7 drift detection](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection), [§8 refresh procedure](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#8-periodic-refresh-procedure). All retained as opt-in / wait-for-signal initiatives.

**What** (v1-era framing, retained for context): Convert this from a periodic snapshot into a continuously-maintained artifact that stays in sync with notes/ as new requirements are written or status changes.

**Why deferred** (v1-era): A living model requires every notes-doc author to follow a tagging convention. Adoption is a separate culture change, and trying to do both v1 capture and v1 living-doc tooling at once dilutes both.

**Sketch** (v1-era):

- Notes-doc authors annotate requirements inline: `<!-- req: JR-CAS-WS-014 status:in-progress -->`
- A scheduled (or PR-triggered) extractor reads these tags + any new untagged candidates, regenerates `notes/requirements/`, and opens a PR with the diff.
- The CI lint catches new requirement-shaped content that wasn't tagged.

### 10.2 Sources beyond notes/

The following sources contain real requirement-shaped content but are deferred from v1.

| Source                                             | Why deferred                                                                                                                                            | Promote when                                                                                                                      |
|:---------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------|
| **PR descriptions**                                | Rich requirement context, but volume is large and history is fragmentary. Triples Phase-3 scope.                                                        | After v1 surfaces the highest-value PRs that the notes/ extraction *cited*, focus a follow-up pass only on those PR descriptions. |
| **`docs/` directories**                            | Polished user-facing docs sometimes encode requirements implicitly ("the API supports X"). Different style, requires separate extraction prompt tuning. | After v1 ships and we have a stable extraction-prompt template that can be adapted.                                               |
| **GitHub issues**                                  | High signal for `proposed` status entries, but tracking issue lifecycle (open/closed/superseded) is a separate state machine.                           | When the project adopts a more structured issue-template that includes a `JR-` ID field.                                          |
| **Code-level docstrings**                          | Mostly describe what code does, not what it should do. Lower yield.                                                                                     | Probably never as a primary source; useful as a cross-reference during QA.                                                        |
| **Conversation-derived (Slack, email, in-person)** | Not searchable in a structured way.                                                                                                                     | When/if the team adopts a "decision-of-record" practice (e.g. ADRs) that captures conversational outcomes in notes/.              |

### 10.3 Priority field

**v4 status**: **RESOLVED at v2.** Priority field added to schema (P0/P1/P2/P3, source-doc-cue inference). See §5.1 and §11 v2-2 row.

### 10.4 Cross-repo dependency graph

**v4 status**: **NOT BUILT.** No usage signal yet. The `notes:` field on entries captures cross-references in plain text where authors flagged siblings during extraction. A proper graph view (DOT/Mermaid) remains a "build when someone asks for it" item. Listed implicitly under [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §10 anti-patterns](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#10-anti-patterns--things-not-to-do-next) — don't build speculatively.

**Original framing (retained)**: Some requirements depend on others (e.g. canopy's "use juniper-observability register_or_reuse" depends on juniper-observability's "ship register_or_reuse helper"). v1 captures both as independent entries with a `Notes` cross-reference.

---

## 11. Progress tracker

This section is the canonical record of where the effort stands. Update at each phase boundary.

> **2026-05-18 note on `/tmp/` references**: Many phase rows below list outputs at paths like `/tmp/req_extract_*.yaml`, `/tmp/phase4_consolidate.py`, `/tmp/v2_citation_validate.py`, etc. The YAML *output* artifacts were consumed into the snapshot at `notes/requirements/` and are recoverable from the snapshot. The Python *source scripts* (`phase4_consolidate.py`, `v2_citation_validate.py`, `v2_apply_citation_fixes.py`, `v4_apply_repairs.py`) are **irrecoverable** — the session sandboxes that held them have been reaped. See §12 entry #19 for the formal carry-over and the rebuild plan. This incident is the basis for the ecosystem-wide Script-placement rule added 2026-05-18 forbidding `/tmp/` as the home for utility scripts (see this repo's [`AGENTS.md` § Script placement](../AGENTS.md#script-placement-mandatory); the same rule is restated in the parent `Juniper/AGENTS.md` "Cross-Project Conventions" section).

### Phase status

| Phase | Status | Started | Completed | Output | Notes |
|---|---|---|---|---|---|
| 0 — Plan | ✅ done | 2026-05-11 | 2026-05-11 | This document | Decisions locked per §3 |
| 1 — Inventory | ✅ done | 2026-05-12 | 2026-05-12 | `/tmp/notes_inventory_2026-05-11.{md,tsv}` | First agent's `.md` was partially hallucinated; rebuilt from authentic TSV via Bash. TSV row counts cross-validated against filesystem. See Phase-1 results table below. |
| 2 — Schema lock | ✅ done | 2026-05-12 | 2026-05-12 | (this doc, updated §5/§5.1/§6) | `Priority` field added (P0-P3, source-doc-cue inference); area-code enum locked at 15 codes (10 original + ARCH/PERF/TOOL/DOC/OPS). |
| 3 — Extraction (pilot: juniper-ml) | ✅ done | 2026-05-12 | 2026-05-12 | `/tmp/req_extract_juniper-ml_2026-05-11.yaml` (635 entries, disposable) | Pilot calibration: discovered Approach-A/B/C sub-bullet inflation (~30-40% of entries were sub-bullets of single decisions). Rule 4 (consolidate-per-decision-block) added to common brief before fan-out. Pilot extraction discarded. |
| 3 — Extraction (full fan-out, 10 parallel agents) | ✅ done | 2026-05-12 | 2026-05-12 | `/tmp/req_extract_{ml-A,ml-B,ml-C,cas,can,dat,dep,cwk,ccl,dcl}_2026-05-11.yaml` (1,078 entries) | juniper-ml split into 3 sub-slices (ml-A top-level + small dirs; ml-B interface_proposals + proposals; ml-C development + legacy + code-review + regressions). Many agents truncated processing under context-budget pressure — file coverage was 64/625 (10%). |
| 3b — Gap-fill on uncited score≥50 files | ✅ done | 2026-05-12 | 2026-05-12 | `/tmp/req_extract_3b-{1,2,3,4}_2026-05-11.yaml` (238 entries) | Triggered by Phase-3 coverage gap: 37 files with density score ≥50 were not cited at all, including 14 of 15 interface_proposals/ R-round files. 4 small parallel agents processed 34 of 36 high-priority gap files; ~98% score-≥50 coverage afterward. |
| 4 — Consolidation | ✅ done | 2026-05-12 | 2026-05-12 | `notes/requirements/**`, `notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`, `notes/requirements/id_assignments.yaml` | 1,316 candidates → 1,033 dedupe-merged entries via (owner, category, normalized-brief) bucketing. 283 duplicates collapsed. 31 markdown files + 1 YAML written (15 by-area + 8 by-repo + 7 by-status + README + index). Run via `/tmp/phase4_consolidate.py`. |
| 5 — QA | ✅ done | 2026-05-12 | 2026-05-12 | (findings appended below) | Path/line-range validity 20/20, content fidelity 5/5 spot-check, citation-precision 4/5 (one entry's line range pointed to threat-discussion section while the actual spec was elsewhere in the same file). v1 acceptable. |
| 6 — Ship | ✅ done | 2026-05-12 | 2026-05-13 | PR #255, merge commit `5705aaff` | Merged to juniper-ml main 2026-05-13. 34 files, 45,085 insertions. See Phase-6 ship record below. |
| **v2-1 — Citation validation diagnostic** | ✅ done | 2026-05-14 | 2026-05-14 | `/tmp/v2_citation_validate.py` + `/tmp/v2_apply_citation_fixes.py` | Diagnostic across all 1033 v1 entries: 98.3% EXACT, 0.3% NEAR, 1.0% DRIFT, 0% NO_MATCH. Spot-check 5-sample 20%-bad estimate was sampling noise; population precision was excellent. Fixed 8 entries (4 BAD_RANGE off-by-ones, 2 BAD_PATH where one of two sources was fabricated, 2 line_end=None drops) via source-YAML edits + re-consolidation. §12-#2 downgraded from Medium to Low. |
| **v2-2 — Phase 3c mid-density gap-fill** | ✅ done | 2026-05-14 | 2026-05-14 | `/tmp/req_extract_3c-{1,2a,2b,3a,3a-2,3b,3b-2,4}_2026-05-11.yaml` (804 new entries) | 6 initial agents + 2 follow-ups on truncated slices. 218 mid-density (score 10-49) files in scope; 189 processed (87%). 3c-2b alone yielded 541 entries (code-review files were dense). Ecosystem file coverage now ~330/625 = 53% (was 23% in v1). 3c-3b-2 used 6 invalid category codes; auto-remapped (AR→ARCH, BG→TRAIN, CI→TEST, CL→TOOL, SE→API, TI→TEST). |
| **v2-3 — Cross-repo content dedup** | ✅ done (limited) | 2026-05-14 | 2026-05-14 | `phase4_consolidate.py` enhanced | Added pre-pass that merges entries with same normalized brief AND same source-basename tuple but different owners. **0 hits** — heuristic too strict. Looser matching (fuzzy brief overlap) deferred to v3 because many same-basename cross-repo pairs are NOT real dups (e.g., `AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` exists in juniper-cascor-client AND juniper-data-client; each is a legitimately separate per-repo audit). Real cross-repo dup potential exists (60 entries cite `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` across ml + can owners). New v3 issue in §12. |
| **v2-4 — ARCH re-bucket** | ✅ done | 2026-05-14 | 2026-05-14 | `phase4_consolidate.py` enhanced | Added post-dedup pass that scans ARCH entries for strong WS/SEC/PERF/TEST/UI/OBS/API/TRAIN/DATA/LOCK/DEP/OPS/DOC/TOOL keyword signal in brief+detail. 148 entries moved out of ARCH (target distribution: TRAIN=58, WS=29, TEST=11, SEC=10, PERF=10, OBS=9, DATA=6, UI=6, TOOL=5, API=2, DOC=2). ARCH dropped from 42% of corpus to ~24%. |
| **v2-ship — Regenerate + PR** | ✅ done | 2026-05-14 | 2026-05-14 | PR #257, merge commit `d4bcf5e` | v2 corpus: 2,120 candidates → 1,801 entries (319 dedup'd). 768 net new requirements vs v1's 1,033. 33 files modified, 51,006 insertions / 15,604 deletions. |
| **v3-1 — Fuzzy cross-repo dedup** | ✅ done | 2026-05-14 | 2026-05-14 | `phase4_consolidate.py` | Replaced v2-3's exact-match heuristic with overlap-coefficient ≥ 0.65 on brief tokens within same-basename clusters. **9 cross-repo pairs collapsed.** Most "cross-repo dups" turned out to be different parts of the same shared document extracted independently (e.g., FINAL_CANOPY_CASCOR has 60 entries from can+ml but only 3 cross-owner pairs at any non-trivial similarity — confirms §12-#10 hypothesis that fuzzy match without manual review correctly handles the per-repo-AGENTS-audit case). |
| **v3-2 — Cross-round R0-R4 dedup** | ✅ done | 2026-05-14 | 2026-05-14 | `phase4_consolidate.py` | Added fuzzy dedup within (owner, category) buckets where ≥1 cited source is in interface_proposals/R[0-4]-*.md. **17 cross-round pairs collapsed.** Smaller-than-expected impact because ml-B's R3-03 anchor strategy already prevented most cross-round duplication at extraction time. |
| **v3-3 — Thin-brief cleanup** | ✅ done | 2026-05-14 | 2026-05-14 | `phase4_consolidate.py` | Scanned for header-pattern + too-short briefs (regex against numbered-section / sub-section / single-word-label patterns). **32 entries dropped** (pure-header entries where cited range was ≤ 3 lines). **355 briefs repaired** by reading cited line range and extracting first content-like line (skipping headers, bullets, code fences). **139 entries flagged** as unrepairable (cited range only contained headers). Highest-impact v3 sub-item by quality delta; surfaced that 25.4% of v2 entries had header-pattern briefs. |
| **v3-4 — ARCH rule refinement** | ✅ done (no-op) | 2026-05-14 | 2026-05-14 | (no change) | v2-4 re-bucket rules already brought ARCH from 42% → 24% of corpus. Spot-check showed no obvious mis-classifications. v3 kept v2 rules unchanged; further refinement deferred to v4 if needed. |
| **v3-ship — Regenerate + PR** | ✅ done | 2026-05-14 | 2026-05-15 | PR #259, merge commit `ab968dd` | v3 corpus: 2,120 candidates → 1,773 entries. -28 vs v2 (28 cross-repo/cross-round dedups), but **355 briefs repaired** and **32 junk entries dropped** — quality delta dominates count delta. Citation precision: 97.3% EXACT on the cleaner corpus. 28 files modified, 21,197 insertions / 17,666 deletions. |
| **v4-1 — LLM brief repair of 119 thin briefs** | ✅ done | 2026-05-15 | 2026-05-15 | `/tmp/v4_thin_brief_repairs.yaml` + `/tmp/v4_apply_repairs.py` | One Explore agent processed all 119 v3-flagged entries. Read each entry's cited line range and wrote a proper 1-sentence requirement brief. 119 repaired, 0 deleted, 0 still flagged. Source-YAML edits applied via JR-ID → source-citation match. |
| **v4-2 — Phase-3d canopy mid-density gap-fill** | ✅ done | 2026-05-15 | 2026-05-15 | `/tmp/req_extract_3d-1_2026-05-11.yaml` (29 entries) | One Explore agent processed the 29 canopy mid-density files (score 10-49) that 3c-3a + 3c-3a-2 left uncovered. Files fully scope-covered (29/29). |
| **v4-3 — Heuristic brief-repair refinement** | ✅ done | 2026-05-15 | 2026-05-15 | `phase4_consolidate.py` | Replaced first-content-line picker with a scoring system. Lines with strong verb hints (must/shall/add/fix/...) score +5; capital-letter starts +2; long lines +1; table-row and ALL-CAPS skipped. Reduced auto-flagged thin briefs from 139 to 119 standalone (the remaining 119 then handled by v4-1). |
| **v4-ship — Regenerate + PR** | ✅ done | 2026-05-15 | 2026-05-15 | PR #261, merge commit `c005d7b` | v4 corpus: 2,149 candidates → **1,803 entries**. +30 vs v3 (29 from v4-2, +1 dedup variance). **118 briefs explicitly repaired by v4-1.** Citation precision: **97.7% EXACT** (up from 97.3% in v3). 25 files modified, 18,053 insertions / 14,224 deletions. |
| **v5-1 — Rebuild the consolidation script** | ✅ done | 2026-08-21 | 2026-08-21 | `util/requirements_consolidate.py` | The §8 hard prerequisite, discharged. NOT a reimplementation of `phase4_consolidate.py`: the Phase-3 extraction YAMLs it consumed were also `/tmp`-resident and are gone, so the corpus now comes from the shipped views. Two findings forced the design — `id_assignments.yaml` has **no `detail` field**, so regenerating views from the ledger would delete 910 Detail sections; and the three view families disagree with each other on the shipped corpus (52 entries by-area vs by-repo, 149 by-area vs by-status, by-area carrying a spurious trailing period), so regenerating any family from another propagates a defect. The script is therefore append-only and re-emits entry bodies verbatim, with `--check-roundtrip` asserting byte-identical render(parse(x)) across all 30 view files. **CORRECTION 2026-08-29 (ml#1415 / ml#1462):** the row's COUNTS reproduce exactly (52 / 149) — what is false is its INFERENCE. The three families differ by ZERO ids and ZERO metadata fields; the 52/149 are trailing punctuation, whitespace and markdown artifacts on otherwise identical entries, reducing to four (since repaired, ml#1467), so regenerating one family from another propagates nothing. `by-repo`/`by-status` are now a GENERATED projection of `by-area`, gated by `--check-views`. Also: `--check-roundtrip` asserts across the **15** `by-area` files, not "all 30 view files" — the other 16 are `--check-views`'s. |
| **v5-2 — `rec` owner block (Q-12 / Wave 7.6)** | ✅ done | 2026-08-21 | 2026-08-21 | `notes/requirements/v5_rec_extraction.yaml`, `by-repo/rec.md` | Refresh trigger: *"a new major repo joins the ecosystem"* — `juniper-recurrence` postdates the snapshot. Citation drift measured **0.00% (1,915/1,915 OK)**, so per §8 the scope was a minimal refresh plus the new block, with no re-extraction. 11 entries generated from the ratified proposal by `util/ad-hoc/2026-08-21_v5_rec_extraction.py` rather than transcribed. |
| **v5-ship — Regenerate + PR** | ✅ done | 2026-08-21 | 2026-08-21 | 12 files | v5 corpus: **1,814 entries** (+11 vs v4). Diff is purely additive — every deleted line is a stat-header recount; no entry text was removed. Gate: `tests/test_requirements_consolidate.py` (17 tests). |

### Decisions made during execution

(append entries here as work proceeds)

| Date | Decision | Rationale | Phase |
|---|---|---|---|
| 2026-05-11 | All five plan-locking questions answered (see §3) | Reviewed by owner | 0 |
| 2026-05-12 | First Phase-1 inventory agent produced authentic TSV but hallucinated `.md` report (chat summary self-contradicted with the file). Discarded `.md`; rebuilt deterministically from TSV via Bash with row-count and LOC/score sample cross-validation against filesystem. | Hallucination caught early; TSV is the canonical Phase-1 artifact. Reinforces §8 risk: Explore agents may fabricate summary tables independently from their search results. Phase-3 extraction agents must therefore produce machine-checkable artifacts (YAML with source line ranges) — never free-form prose — to make hallucination detectable by post-hoc grep. | 1 |
| 2026-05-12 | Added required `Priority` field to schema (P0-P3, source-doc-cue inference; see §5.1). | Total Phase-1 density score is 12,926 keyword hits across 625 files → conservative 3-5 hits/req → 2,500-4,300 candidate requirements pre-dedup. Well over the 1,500 threshold in §3-Q2 that triggers the priority field. Without priority, the index is unnavigable at this volume. | 2 |
| 2026-05-12 | Locked the area-code enum at 15 codes: the original 10 (OBS, SEC, API, DEP, UI, DATA, TRAIN, WS, TEST, LOCK) plus 5 new (ARCH, PERF, TOOL, DOC, OPS). | Phase-1 top-density files include large bodies of architectural design work (interface_proposals/R1-R5, microservices roadmap), performance/scalability roadmaps, operational runbooks, dev-tooling procedures (worktree, claudey), and process documentation (link validation, conventions). The original enum had no clean home for these and would have forced lossy bucketing. Phase 4 may still add codes after dedup if needed. | 2 |

### Phase-1 inventory results (filled in 2026-05-12)

Source: `/tmp/notes_inventory_2026-05-11.{md,tsv}` (TSV verified against filesystem; `.md` rebuilt deterministically from TSV after the first agent's hallucinated draft).

| Repo                  | notes file count | total LOC   | total density score | top file (score)                                                 |
|-----------------------|------------------|-------------|---------------------|------------------------------------------------------------------|
| juniper-ml            | 262              | 152,718     | 7,834               | interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md (469)           |
| juniper-canopy        | 133              | 58,334      | 2,243               | TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md (166)            |
| juniper-cascor        | 114              | 55,338      | 2,045               | development/DEVELOPMENT_ROADMAP.md (238)                         |
| juniper-data          | 47               | 13,830      | 500                 | JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-17.md (73) |
| juniper-deploy        | 23               | 5,612       | 206                 | SLO_CATALOG_2026-05-03.md (66)                                   |
| juniper-cascor-worker | 17               | 2,262       | 44                  | JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md (7)                             |
| juniper-cascor-client | 14               | 1,839       | 26                  | JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md (7)                             |
| juniper-data-client   | 15               | 1,737       | 28                  | JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md (7)                             |
| **Total**             | **625**          | **291,670** | **12,926**          | —                                                                |

**Top 5 cross-repo files by density** (Phase-3 priority seed):

1. `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (469, 1,626 LOC)
2. `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (461, 1,363 LOC)
3. `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (450, **15,220 LOC** — by far the largest file)
4. `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (365, 1,464 LOC)
5. `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (324, 5,458 LOC)

**Observations driving Phase-2 decisions**:

- **Density skew**: juniper-ml alone holds 7,834 of 12,926 (61%) of total density; together with juniper-canopy + juniper-cascor, the top 3 repos hold 96% of ecosystem density. Phase-3 fan-out can de-prioritize the 4 low-density client/worker repos (each <50 total score) — those agents will be quick.
- **Two huge documents**: V7 IMPLEMENTATION_ROADMAP (15,220 LOC) and V6 REMEDIATION_ANALYSIS (5,458 LOC) in juniper-ml dominate. Each Phase-3 agent must be allowed multiple read passes; these likely cannot be processed in a single read window.
- **interface_proposals/ cluster**: 9 of the top 25 density files are juniper-ml round-N proposal docs (R0/R1/R2/R3/R4/R5). They overlap thematically (WebSocket migration design rounds); Phase-4 dedup will collapse many cross-proposal restatements.
- **10 files >2000 LOC ecosystem-wide**: 8 in juniper-ml, 1 in juniper-cascor (POLYREPO_MIGRATION_PLAN.md, 2,181 LOC), 1 also in juniper-cascor (history/SPIRAL_DATA_GEN_REFACTOR-002.md, 2,690 LOC). Phase-3 agents must chunk these — single read window won't cover the V7 roadmap or V6 remediation.
- **68 files score 0**: boilerplate (BOX_DRAWING_ASCII.md, file-header templates, code-style guides). Phase-3 agents skip these.

### Phase-3 + Phase-3b extraction yields (filled in 2026-05-12)

| Slice                 | Repo                                                                                     | Files in scope     | Files processed        | Pre-dedup entries    | Notes                                                                                                                                                                         |
|-----------------------|------------------------------------------------------------------------------------------|--------------------|------------------------|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ml-A                  | juniper-ml (top-level + obs/releases/docs/concurrency/templates)                         | 71                 | 4                      | 17                   | Severely truncated; agent only handled V7 roadmap + 3 small files. Filled by 3b later.                                                                                        |
| ml-B                  | juniper-ml (interface_proposals/ + proposals/)                                           | 30                 | 30                     | 83                   | Agent anchored on R3-03 (73 of 83 entries from one file); other R-rounds got 1 entry each → 3b-1/3b-2 gap-fill.                                                               |
| ml-C                  | juniper-ml (development + legacy + code-review + regressions + pull_requests + partials) | 161                | 3                      | 705                  | Agent processed only the 3 elephants (V6 remediation 5,458 LOC, R5-01 canonical 2,167 LOC, WebSocket architecture-1 2,154 LOC); 158 files of legacy/regressions/etc. skipped. |
| cas                   | juniper-cascor                                                                           | 114                | 15                     | 45                   | Agent excluded 99 files as "pure historical narrative" per §4. Coverage of forward-looking material reasonable.                                                               |
| can                   | juniper-canopy                                                                           | 133                | 4                      | 95                   | Severely truncated. CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md alone produced 78 entries.                                                                                  |
| dat                   | juniper-data                                                                             | 47                 | 3                      | 39                   | Agent claimed "44 reviewed for completeness" but only cited 3 files.                                                                                                          |
| dep                   | juniper-deploy                                                                           | 23                 | 8                      | 28                   | Reasonable for a small repo. SLO_CATALOG + PHASE2_SYSTEMD dominate.                                                                                                           |
| cwk                   | juniper-cascor-worker                                                                    | 17                 | 17                     | 15                   | Complete coverage. Low-density slice.                                                                                                                                         |
| ccl                   | juniper-cascor-client                                                                    | 14                 | 14                     | 33                   | Complete coverage. AGENTS.md audit/update + release notes dominate.                                                                                                           |
| dcl                   | juniper-data-client                                                                      | 15                 | 9                      | 16                   | 6 boilerplate/score-0 files skipped (legitimate).                                                                                                                             |
| **Phase-3 subtotal**  |                                                                                          | **625**            | **107**                | **1,078**            |                                                                                                                                                                               |
| 3b-1                  | juniper-ml interface_proposals R0/R1 (gap-fill)                                          | 6                  | 6                      | 34                   | Recovered R1-04 (score 469) + 5 R0/R1 siblings.                                                                                                                               |
| 3b-2                  | juniper-ml interface_proposals R2/R3/R4 (gap-fill)                                       | 7                  | 7                      | 20                   | Recovered R2-02 (score 365) + 6 R2/R3/R4 siblings. Heavy under-extraction — agent applied consolidation aggressively.                                                         |
| 3b-3                  | juniper-ml development/code-review/regressions (gap-fill)                                | 12                 | 12                     | 154                  | 45 entries marked `superseded` (V4/V5 snapshots subsumed by V6/V7).                                                                                                           |
| 3b-4                  | legacy/history across 3 repos (gap-fill)                                                 | 11                 | 9                      | 30                   | Historical-narrative exclusion applied strictly per §4. 2 files (CASCOR_DEMO_TRAINING_ERROR_PLAN _1 + -ORIG) treated as dedups of primary.                                    |
| **Phase-3b subtotal** |                                                                                          | **36**             | **34**                 | **238**              |                                                                                                                                                                               |
| **Grand total**       |                                                                                          | **661 file-slots** | **141 distinct files** | **1,316 candidates** | 96 unique files cited; 1,033 entries after Phase-4 dedup.                                                                                                                     |

### Phase-5 QA findings (filled in 2026-05-12)

**Hallucination spot-check (random N=20)**:

- **Path validity**: 20 / 20 — every cited source file exists on disk.
- **Line-range validity**: 20 / 20 — every cited `line_start`/`line_end` falls within the source file's actual line count.
- **Content match (5/20 deep-checked via `sed`)**:
  - 4/5: brief accurately reflects source text at cited line range.
  - 1/5 (JR-ML-SEC-001): content is real (WS frame-size limits 4 KB / 64 KB) but cited line range (JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md §3 lines 145-180, threat discussion) doesn't pinpoint the actual specification block (same file, lines 562-574). Content fidelity preserved; citation precision off. Treat as a moderate Phase-5 finding.
  - 1/20 (JR-ML-ARCH-373): "RISK: Criterion" brief is too thin to be a useful requirement — the cited content is a success-criteria *table header* rather than a constituent decision. Phase-4 consolidation should have rejected or expanded this; flagging for v2.

**Coverage spot-check (high-density files)**:

| File                                                                                            | Density score    | Entries assigned | Note                                                                           |
|-------------------------------------------------------------------------------------------------|------------------|------------------|--------------------------------------------------------------------------------|
| `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`           | 450 (15,220 LOC) | ~4 (ml-A)        | Significantly under-extracted; only sampled tail. v1 known limitation.         |
| `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md`                             | 469              | 34 (3b-1)        | Down from pilot's 133 due to consolidation rule. Some loss; acceptable for v1. |
| `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md`                       | 365              | 13 (3b-2)        | Under-extracted relative to density. Agent over-consolidated.                  |
| `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` | 324 (5,458 LOC)  | 250 (ml-C)       | Heavy coverage as expected (Approach-A/B/C corpus).                            |
| `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md`                              | 235 (2,167 LOC)  | 388 (ml-C)       | Maximum-extraction file; many short C-NN constitution positions.               |

**Verdict**: v1 acceptable. Hallucination defenses held (no fabricated files or invalid line ranges). The two findings (citation-precision drift in #11, thin brief in #7) are Phase-4 quality issues that should be addressed in v2 iteration — not blockers for shipping v1.

### Phase-6 ship record (filled in 2026-05-13)

| Item                         | Value                                                                                                                                              |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| PR                           | [#255](https://github.com/pcalnon/juniper-ml/pull/255)                                                                                             |
| Merge commit                 | `5705aaff5b90f00cdb3592a80e5fb4654575a6b6`                                                                                                         |
| Source branch                | `worktree-validated-weaving-pie` (commit `bbb6848`)                                                                                                |
| Files added                  | 33 (`notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`, `notes/requirements/README.md`, 15 `by-area/*.md`, 8 `by-repo/*.md`, 7 `by-status/*.md`, `id_assignments.yaml`) |
| Files modified               | 1 (`notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md`)                                                                                         |
| Total requirements published | 1,033 (1,316 candidates pre-dedup; 283 collapsed)                                                                                                  |
| Unique source files cited    | 96                                                                                                                                                 |
| Date shipped                 | 2026-05-13                                                                                                                                         |
| Tracker close-out            | This update (separate PR, branch `chore/req-tracker-closeout-2026-05-13`)                                                                          |

---

## 12. Open issues / questions discovered during execution

### v1 issues — status as of v2 ship

| # | Issue                                                                                              | v1 Severity | v2 Resolution                                                                                                                                                                                                                                             |
|---|----------------------------------------------------------------------------------------------------|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | **File coverage 141/625 (23%).** Mid-density (score 10-49) and most score 1-9 files not processed. | Medium      | **PARTIAL** — v2 Phase-3c added 8 agents covering 189 of 218 score-10-49 files (87% mid-density coverage). Ecosystem coverage now ~330/625 = 53%. Score 1-9 files (~245) still unprocessed; deferred to v3 (low value).                                   |
| 2 | **Citation-precision drift** estimated at ~20% from 5-sample.                                      | Medium      | **RESOLVED** — v2-1 full-corpus diagnostic showed actual population precision is 98.3% EXACT; the 5-sample estimate was noise. Downgrade to Low. 8 specific bad-citation entries fixed via source-YAML edits.                                             |
| 3 | **Thin briefs** ("RISK: Criterion", etc.)                                                          | Low         | **NOT ADDRESSED** — carried to v3.                                                                                                                                                                                                                        |
| 4 | **`ARCH` category over-represents at 42%.**                                                        | Low         | **PARTIAL** — v2-4 ARCH re-bucket moved 148 entries to finer codes; ARCH now ~24% of corpus. Some ARCH entries remain that lacked keyword signal for re-bucketing.                                                                                        |
| 5 | **Cross-round dedup conservative** (R0-R4 proposal overlap).                                       | Low         | **NOT ADDRESSED** — carried to v3. Would need fuzzy-match.                                                                                                                                                                                                |
| 6 | **Two `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` files** (ml + canopy).                          | Low         | **NOT ADDRESSED** — v2-3 cross-repo dedup heuristic (require exact normalized brief + same basename tuple) got 0 hits because briefs differ across owners. 60 entries cite this basename across both owners; real dup. Needs fuzzy match — carried to v3. |
| 7 | **Phase-1 agent fabricated its `.md` report.**                                                     | Process     | **APPLIED** — v2 brief reinforced same discipline (machine-checkable YAML only). No agent-summary fabrications detected in Phase-3c.                                                                                                                      |

### New issues discovered during v2 (status updated at v3 ship)

| #  | Issue                                                                 | Severity | v3 status                                                                                                                                                                                                                                                                                  |
|----|-----------------------------------------------------------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 8  | **Phase-3c agents truncated on "elephant" files within their slice.** | Medium   | **NOT ADDRESSED** — agent-brief improvement; only helps future extraction passes. Carried to v4.                                                                                                                                                                                           |
| 9  | **3c-3b-2 invented 6 invalid category codes.**                        | Low      | **NOT ADDRESSED** — agent-brief improvement; only helps future extraction passes. Carried to v4.                                                                                                                                                                                           |
| 10 | **Cross-repo content dedup needs fuzzy match.**                       | Medium   | **RESOLVED** — v3-1 implement overlap-coefficient ≥ 0.65 fuzzy match. Most "cross-repo dups", diff content from same file. 9 dups collapsed across 22 multi-owner basename clusters. `AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` per-repo audits correctly NOT merged (briefs differ enough). |
| 11 | **Score 1-9 long tail (~245 files) unprocessed.**                     | Low      | **NOT ADDRESSED** — cost > benefit; remains out of scope.                                                                                                                                                                                                                                  |
| 12 | **ARCH re-bucket rules first-match heuristic.**                       | Low      | **NOT ADDRESSED (no-op)** — v3 spot-check showed no obvious mis-classifications; rules retained as-is. Carried to v4 only if specific bad cases surface.                                                                                                                                   |

### New issues discovered during v3 (status updated at v4 ship)

| # | Issue | v3 Severity | v4 Resolution |
|---|---|---|---|
| 13 | **139 unrepairable thin briefs from v3** (the residual after v3-3's heuristic). | Low | **RESOLVED** — v4-3's heuristic improvement (verb-scored line selection) auto-cleared ~20 of them; v4-1's LLM agent then re-read each remaining flagged entry's cited range and wrote a proper 1-sentence requirement brief. 119/119 repaired in the v4-1 pass. |
| 14 | **Brief-repair heuristic picks suboptimal content line.** | Low | **RESOLVED** — v4-3 replaced first-eligible-line with a verb-hint + length + capital-start scoring system. |
| 15 | **Cross-round dedup smaller than expected.** | Finding | **N/A** — accepted as an outcome of v2's R3-03 anchor strategy. |
| 16 | **~30 canopy mid-density files uncovered.** | Low | **RESOLVED** — v4-2 Phase-3d agent processed all 29 (fully covered, 29/29). Added 29 new entries. |

### New issues / observations during v4 (status as of v4 ship)

| # | Issue | Severity | Suggested resolution |
|---|---|---|---|
| 17 | **2 thin-brief entries still flagged after v4-1+v4-3** — borderline edge cases the LLM agent couldn't summarize cleanly. | Trivial | Accept as known limit; not worth a v5 just for 2 entries. |
| 18 | **Coverage ceiling effectively reached for v1-v4 scope.** Score 1-9 long-tail files (~245) still unprocessed per §12-#11 (cost > benefit). Ecosystem file coverage is **~360/625 = 58%**, but **~98% density-weighted coverage** (high-density work captured; only boilerplate remains). | None | The corpus is essentially complete for practical purposes. Future work should focus on *use* of the snapshot (linking JR-IDs from PRs, integrating into PR templates), not further extraction. |

### New issues / observations during §3-§4 adoption (status as of 2026-05-18)

| #  | Issue                                                                                              | Severity | Suggested resolution                                                                                                                                                                                                                                                                                                                                                                          |
|----|----------------------------------------------------------------------------------------------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 19 | **v1-v4 tooling scripts authored in `/tmp/` are irrecoverable.** Specifically: `phase4_consolidate.py` (Phase-4 base dedupe + v2-3 cross-repo + v2-4 ARCH rebucket + v3-1 fuzzy + v3-2 cross-round + v3-3/v4-3 brief repair), `v2_citation_validate.py` + `v2_apply_citation_fixes.py` (v2-1 QA), and `v4_apply_repairs.py` (v4-1 LLM-repair applier). Session sandboxes that held these have been reaped. The YAML *output* artifacts they produced are recovered in the snapshot at `notes/requirements/`, but the source code cannot be recovered. | Medium | **v5 prerequisite — rebuild from scratch.** Consolidate script → `util/requirements_consolidate.py` using §11 phase-row descriptions as the spec (estimated ~600-800 LOC). Citation validator → subsumed into `util/requirements_drift_check.py` (`--mode full` per [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §7](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection)). The `--mode quick` slice shipped 2026-05-18 alongside this entry. Process fix: ecosystem-wide Script-placement rule (parent `Juniper/AGENTS.md` "Cross-Project Conventions"; restated in this repo's [`AGENTS.md` § Script placement](../AGENTS.md#script-placement-mandatory)) now prohibits `/tmp/` for utility scripts; see [`util/ad-hoc/README.md`](../util/ad-hoc/README.md) for the per-script convention. |

### Final dispositions (consolidated 2026-05-18)

Each carry-over issue above receives a permanent disposition here. Sourced from [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §9](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#9-12-carry-over-triage). Future refreshes should treat these as closed unless new evidence reopens them.

| #   | Carry-over                                   | Final disposition                       | Rationale                                                            |
|-----|----------------------------------------------|-----------------------------------------|----------------------------------------------------------------------|
| #8  | Phase-3c agents truncated on elephant files  | **DEFER permanently**                   | Agent-brief improvement; only helps future extraction. None planned. |
| #9  | 3c-3b-2 invented invalid category codes      | **DEFER permanently**                   | Same as #8 — extraction-time concern only.                           |
| #11 | Score 1-9 long-tail (~245 files) unprocessed | **REJECT permanently**                  | Cost > benefit; boilerplate content. v1 decision reaffirmed at v4.   |
| #12 | ARCH re-bucket rules first-match heuristic   | **ACCEPT as-is**                        | v3 spot-check showed no obvious misclassifications.                  |
| #17 | 2 thin-brief entries still flagged after v4  | **ACCEPT as-is**                        | Trivial residual; not worth a v5 for 2 entries.                      |
| #18 | Coverage ceiling reached                     | **FRAMING DECISION (not a defect)**     | Reframes future work toward *use* of the snapshot.                   |
