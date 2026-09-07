# Juniper Requirements — Output Tree

This directory is the consolidated, deduplicated snapshot of all explicit and (aggressive-threshold) implicit requirements identified across the active Juniper repositories' `notes/` directories.

**Current revision: v5 (2026-08-21)** — 1,814 entries. v1–v4 covered the 8 repos active as of 2026-05-12; **v5 added the `rec` owner block** (`juniper-recurrence`, 11 entries) because that repo joined the ecosystem after the snapshot froze, which is the §8 *"a new major repo joins the ecosystem"* refresh trigger. Citation drift measured 0.00% (1,915/1,915 OK) before v5 and 0.00% (1,934/1,934) after, so per §8 the scope was a minimal refresh plus the new owner block — no re-extraction of the existing corpus.

**Source plan**: `../JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md`
**Top-level navigation**: `../JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`

---

## Schema reference

Each requirement entry includes:

| Field | Required | Meaning |
|---|---|---|
| `ID` (`JR-<REPO>-<AREA>-<NNN>`) | yes | Permanent reference ID; never reused even if superseded/rejected |
| `Status` | yes | One of: `proposed`, `designed`, `in-progress`, `shipped`, `deferred`, `rejected`, `superseded` |
| `Priority` | yes | One of: `P0`, `P1`, `P2`, `P3`. Inferred from source-doc language per plan §5.1 |
| `Category` | yes | One of the 15 locked area codes (see below) |
| `Owner` | yes | Canonical owning repo (cas/can/dat/dep/ml/cwk/ccl/dcl/rec) |
| `Sources` | yes (≥1) | List of source-doc paths with line ranges. Hallucination check anchor |
| `Detail` | when non-trivial | Multi-line description |
| `Design` | optional | Design sketch from source doc |
| `PRs` | optional | Only PRs explicitly named in source |
| `Notes` | optional | Cross-references, dedup hints, sibling entries |

## Locked area codes (15)

| Code | Scope |
|---|---|
| `OBS` | observability — metrics, logging, tracing, dashboards, alerting |
| `SEC` | security — authn, authz, secrets, CVEs, hardening |
| `API` | API contracts — schemas, versioning, compatibility, migrations |
| `DEP` | deployment-config — Docker, Compose, K8s, Helm, image build |
| `UI` | ui-frontend — Canopy/Dash, UX, visualizations |
| `DATA` | data-pipeline — dataset generation, NPZ contracts, ingestion |
| `TRAIN` | training — cascor algorithm, candidates, convergence, model state |
| `WS` | websocket / messaging — Canopy↔Cascor streaming, replay, control plane |
| `TEST` | testing-and-ci — pytest, fixtures, CI workflows, regression analysis |
| `LOCK` | lockfile-and-deps — uv lockfiles, pyproject pins, dep updates, env rebuilds |
| `ARCH` | architecture / cross-cutting design — microservices, polyrepo, interface proposals |
| `PERF` | performance / scalability — throughput, latency, parallelization, CUDA |
| `TOOL` | dev tooling / scripts / workflow — worktree procs, claude-code launchers |
| `DOC` | documentation / process — link validation, conventions, file headers |
| `OPS` | operations / runbooks / on-call — runbook documents, incident response |

## Navigation

- **By area**: `by-area/<CODE>.md`
- **By owning repo**: `by-repo/<shortcode>.md`
- **By status**: `by-status/<status>.md`
- **ID lookup**: `id_assignments.yaml`

## Querying

For worked recipes ("open P0/P1 SEC entries", "requirements citing file X", per-area / per-repo / per-status views) see [`../JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §3](../JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#3-snapshot-consumption-recipes). It also lists what *not* to do (e.g., don't grep `id_assignments.yaml` for content — briefs are truncated; don't link to line numbers in `by-area/*.md` — they shift on regen).

## Coverage and limitations

This is a **v1 snapshot**, not a living document. Specifically:

- Source files cited: see plan §11 for Phase-3 + Phase-3b coverage breakdown.
- Phase-3 fan-out covered only ~10% of in-scope files; Phase-3b gap-fill brought score≥50 coverage to ~98%. Files with density score 10-49 (~219 files) remain unprocessed in v1 — this is a documented limitation per plan §10.
- Cross-round restatements in `interface_proposals/` may produce sibling entries with overlapping content; merged entries cite their dedup history via the *Merged from* footer.
- The `ARCH` category is over-represented (~55%) because the locked-enum mapping treated many cross-cutting decisions as `ARCH`. Future iterations may re-bucket some `ARCH` entries into finer categories.

## Updating

The v1–v4 consolidator (`/tmp/phase4_consolidate.py`) is **gone** — it was authored in `/tmp/` and is irrecoverable. The v5 tool is [`util/requirements_consolidate.py`](../../util/requirements_consolidate.py).

**Do not regenerate views from `id_assignments.yaml`.** The ledger has no `detail` field; `by-area/*.md` is the corpus of record. Operator contract: [`docs/REFERENCE.md` § Requirements Snapshot Consolidation](../../docs/REFERENCE.md#requirements-snapshot-consolidation).

```bash
python3 util/requirements_consolidate.py --check-roundtrip
python3 util/requirements_consolidate.py --check-views
python3 util/requirements_consolidate.py --merge notes/requirements/<extraction>.yaml   # dry-run
python3 util/requirements_consolidate.py --merge notes/requirements/<extraction>.yaml --apply
```

`--check-roundtrip` covers the 15 `by-area` files only. `--check-views` asserts `by-repo` / `by-status` are the projection of `by-area`. Default is dry-run; `--apply` writes. A new major repo still needs an extraction YAML first — there is no auto-discovery of untracked notes.
