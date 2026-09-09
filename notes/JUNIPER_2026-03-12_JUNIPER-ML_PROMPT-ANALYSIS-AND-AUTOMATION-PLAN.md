# Juniper Prompt Analysis and Automation Plan

**Version**: 1.0.0
**Date**: 2026-03-12
**Author**: Paul Calnon + Claude Code
**Status**: Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Prompt Inventory](#2-prompt-inventory)
3. [Structural Analysis](#3-structural-analysis)
4. [Common Patterns and Redundancy](#4-common-patterns-and-redundancy)
5. [Natural Prompt Type Boundaries](#5-natural-prompt-type-boundaries)
6. [Automation Approaches](#6-automation-approaches)
7. [Implementation Details](#7-implementation-details)
8. [Risk Analysis and Guardrails](#8-risk-analysis-and-guardrails)
9. [Approach Comparison Matrix](#9-approach-comparison-matrix)
10. [Recommendations](#10-recommendations)
11. [Appendices](#11-appendices)

---

## 1. Executive Summary

This document presents a comprehensive analysis of all Juniper project prompts across two primary locations (`juniper-ml/prompts/` and `Juniper/prompts/`), totaling **~138 markdown files** spanning December 2025 through March 2026. The analysis identifies structural patterns, redundancies, and natural type boundaries, then evaluates multiple automation approaches for prompt creation, modification, and use.

### Key Findings

- **6 distinct prompt types** emerge naturally from the corpus (Handoff, Task, Template, Planning, Audit, Infrastructure)
- **40-70% of prompt content is boilerplate** (60-70% for named templates, 20-40% for task/planning prompts) that could be generated from templates + contextual data
- **Existing infrastructure** (`wake_the_claude.bash`, session persistence) provides a strong foundation for automation
- **A template-driven approach with environment discovery** offers the best balance of automation, transparency, and maintainability

### Scope

| Location                       | Files                       | Size        | Date Range                 |
|--------------------------------|-----------------------------|-------------|----------------------------|
| `juniper-ml/prompts/`          | 28 active + 1 JSON artifact | 328 KB      | Feb 25 – Mar 12, 2026      |
| `Juniper/prompts/` (top-level) | 9 active                    | 34 KB       | Mar 5 – Mar 7, 2026        |
| `Juniper/prompts/` (archives)  | 94+ historical              | 806 KB      | Dec 6, 2025 – Feb 18, 2026 |
| **Total**                      | **131+**                    | **~1.2 MB** | **Dec 2025 – Mar 2026**    |

---

## 2. Prompt Inventory

### 2.1 Active Prompts by Location

#### juniper-ml/prompts/ (28 files)

| #     | Filename                          | Type           | Target                  | Focus                                 |
|-------|-----------------------------------|----------------|-------------------------|---------------------------------------|
| 001   | `prompt001_2026-02-25.md`         | Task           | All repos               | CI dependency documentation           |
| 002   | `prompt002_2026-02-25.md`         | Planning       | cascor, canopy, deploy  | Microservices architecture evaluation |
| 003   | `prompt003_2026-02-25.md`         | Task           | All repos               | Worktree directives in CLAUDE.md      |
| 004   | `prompt004_2026-02-25.md`         | Task           | All repos               | Polyrepo migration validation         |
| 005   | `prompt005_2026-02-25.md`         | Planning       | canopy                  | Canopy repo naming analysis           |
| 006   | `prompt006_2026-02-25.md`         | Task           | All repos               | PyPI publish setup                    |
| 007   | `prompt007_2026-02-25.md`         | Infrastructure | juniper-ml              | Slack MCP server setup                |
| 008   | `prompt008_2026-02-26.md`         | Infrastructure | juniper-ml              | Slack-to-Claude connection            |
| 009   | `prompt009_2026-02-26.md`         | Template       | juniper-ml              | New project setup template            |
| 010   | `prompt010_2026-03-02.md`         | Audit          | All repos               | Full documentation audit              |
| 011   | `prompt011_2026-03-02.md`         | Infrastructure | juniper-ml              | Slack startup diagnostic              |
| 012   | `prompt012_2026-03-02.md`         | Audit          | All repos               | Microservices roadmap audit           |
| 013   | `prompt013_2026-03-02.md`         | Task           | All repos               | Polyrepo migration continuation       |
| 014   | `prompt014_2026-03-02.md`         | Task           | All repos               | Juniper startup documentation         |
| 015   | `prompt015_2026-03-02.md`         | Audit          | All repos               | Documentation audit iteration         |
| 016   | `prompt016_2026-03-03.md`         | Planning       | All repos               | Doc audit & enhancement planning      |
| 016.1 | `prompt016.1_2026-03-03.md`       | Handoff        | All repos               | Doc gen continuation handoff          |
| 016.2 | `prompt016.2_2026-03-03.md`       | Planning       | All repos               | Comprehensive doc plan (101 KB)       |
| 016.3 | `prompt016.3_2026-03-03.md`       | Handoff        | All repos               | Phase 6 validation handoff            |
| 017   | `prompt017_2026-03-03.md`         | Task           | cascor                  | Test issues investigation             |
| 018   | `prompt018_2026-03-03.md`         | Task           | cascor                  | Cascor test deep-dive                 |
| 019   | `prompt019_2026-03-03.md`         | Planning       | deploy                  | Docker Python 3.14 migration          |
| 020   | `prompt020_2026-03-03.md`         | Task           | deploy                  | Docker Compose launch failures        |
| 021   | `prompt021_2026-03-04.md`         | Task           | deploy                  | Docker package additions              |
| 022   | `prompt022_2026-03-11.md`         | Task           | juniper-ml, data-client | Worktree cleanup + PR #58             |
| 023   | `prompt023_2026-03-11.md`         | Task           | juniper-ml, data-client | Cleanup continuation                  |
| —     | `prompt-automation_2026-03-12.md` | Planning       | juniper-ml              | This analysis prompt                  |

#### Juniper/prompts/ Top-Level (9 files)

| #   | Filename                  | Type           | Target       | Focus                        |
|-----|---------------------------|----------------|--------------|------------------------------|
| 001 | `prompt001_2026-03-05.md` | Planning       | cascor       | Architectural Design Journal |
| 002 | `prompt002_2026-03-05.md` | Task           | deploy       | Container validation + CI    |
| 003 | `prompt003_2026-03-05.md` | Task           | All services | Docker migration cleanup     |
| 004 | `prompt004_2026-03-05.md` | Planning       | All repos    | Observability infrastructure |
| 005 | `prompt005_2026-03-05.md` | Infrastructure | juniper-ml   | Slack MCP server             |
| 006 | `prompt006_2026-03-05.md` | Infrastructure | juniper-ml   | Slack-to-Claude.ai           |
| 007 | `prompt007_2026-03-05.md` | Task           | All repos    | Key rotation (SOPS)          |
| 008 | `prompt008_2026-03-07.md` | Handoff        | juniper-ml   | Script fixes handoff         |
| 009 | `prompt009_2026-03-07.md` | Handoff        | juniper-ml   | Cross-repo link resolution   |

#### Historical Archives (4 directories, 94+ files)

| Directory                           | Files | Date Range     | Focus                        |
|-------------------------------------|-------|----------------|------------------------------|
| `history-prompts_2025-12-31/`       | 7     | Dec 6–31, 2025 | Initial project setup        |
| `history-prompts_2026-01-31/`       | 56    | Jan 2–31, 2026 | Core development phase       |
| `history-prompts_2026-02-28/`       | 16    | Feb 2–18, 2026 | Transition work              |
| `history-named-prompts_2026-02-06/` | 12    | Curated set    | Reusable task templates (v1) |
| `history-named-prompts_2026-03-05/` | 12    | Curated set    | Reusable task templates (v2) |

### 2.2 Target Project Coverage

| Project               | Prompt Count | Primary Themes                                |
|-----------------------|--------------|-----------------------------------------------|
| juniper-cascor        | 28           | Architecture, testing, neural network backend |
| juniper-canopy        | 24           | Dashboard, docs, Docker                       |
| juniper-ml            | 24           | Meta-package, tooling, automation             |
| juniper-data          | 16           | Microservice, documentation                   |
| juniper-deploy        | 11           | Docker Compose, CI/CD                         |
| juniper-cascor-client | 6            | Client library                                |
| juniper-cascor-worker | 4            | Distributed training                          |
| juniper-data-client   | 3            | Client library                                |
| Cross-ecosystem       | 12           | Migration, infrastructure                     |

---

## 3. Structural Analysis

### 3.1 Identified Section Patterns

Analysis of all 131+ prompts reveals a convergent set of section headers. The following table shows section frequency by prompt type:

| Section Header              | Handoff | Task | Template | Planning | Audit | Infra | Overall |
|-----------------------------|---------|------|----------|----------|-------|-------|---------|
| H1 Title                    | 100%    | 100% | 100%     | 100%     | 100%  | 100%  | 100%    |
| Role                        | 0%      | 30%  | 100%     | 40%      | 60%   | 20%   | 42%     |
| Overview / Background       | 20%     | 60%  | 80%      | 90%      | 80%   | 70%   | 67%     |
| Primary Objective           | 10%     | 70%  | 100%     | 80%      | 90%   | 60%   | 68%     |
| Resources                   | 0%      | 30%  | 100%     | 40%      | 60%   | 20%   | 42%     |
| Assigned Tasks / Directives | 0%      | 80%  | 100%     | 70%      | 90%   | 80%   | 70%     |
| Key Deliverables            | 0%      | 50%  | 100%     | 60%      | 80%   | 40%   | 55%     |
| Completed So Far            | 100%    | 10%  | 0%       | 10%      | 0%    | 0%    | 20%     |
| Remaining Work              | 100%    | 10%  | 0%       | 10%      | 0%    | 0%    | 20%     |
| Key Context                 | 100%    | 20%  | 0%       | 20%      | 10%   | 10%   | 27%     |
| Verification Commands       | 90%     | 30%  | 0%       | 20%      | 30%   | 30%   | 33%     |
| Git Status                  | 85%     | 10%  | 0%       | 10%      | 0%    | 0%    | 18%     |

### 3.2 Content Format Patterns

**Formatting conventions observed across all prompts:**

| Element         | Convention                                              | Frequency |
|-----------------|---------------------------------------------------------|-----------|
| Headers         | H1 for title, H2 for sections, H3/H4 for subsections    | 100%      |
| Lists           | Numbered for sequential tasks, bullets for requirements | 95%       |
| Code blocks     | Bash fenced blocks for commands                         | 80%       |
| Tables          | Markdown tables for comparison/status                   | 45%       |
| Separators      | `---` between major sections                            | 60%       |
| Placeholders    | `<variable-name>` in angle brackets                     | 70%       |
| Path references | Mix of absolute and relative paths                      | 90%       |
| Line references | `(line N)` or `(line N-M)` format                       | 25%       |

### 3.3 Metadata Patterns

**Current state: No formal metadata system exists.** Prompts contain no YAML/TOML frontmatter. Metadata is implicit in:

- Filename: `promptNNN_YYYY-MM-DD.md` (number + date)
- Named files: `promptNN_UPPERCASE_SNAKE_CASE.md` (number + category)
- Content: Target project references are embedded in prose
- Location: Directory determines active vs. archived status

### 3.4 Boilerplate Analysis

**High-frequency boilerplate blocks identified across the named template prompts:**

1. **Role Definition Block** (~100-200 words, appears in 75% of named prompts):

   ```bash
   You are a helpful and experienced Software Engineer with extensive
   experience in Machine Learning and Artificial Intelligence. You approach
   problems logically and systematically, breaking them down into smaller,
   more manageable parts. You develop a plan prior to starting any task...
   ```

2. **Code Change Approval Disclaimer** (~80 words, appears in 83% of named prompts):

   ```bash
   Make NO code changes to the Juniper [application] without my explicit,
   and change-specific approval--this does NOT apply to tests. When making
   code changes that involve deleting or changing an existing line, the
   original line should be commented out...
   ```

3. **Resources Utilization Block** (~60 words, appears in 83% of named prompts):

   ```bash
   Tasks should be completed accurately and thoroughly by utilizing all
   available resources including, but not limited to:
   - Use sub-agents as needed
   - Use external and web sources as needed
   - Use the Juniper documentation sources and application API...
   ```

4. **Handoff Section Template** (~150-300 words, appears in all handoff prompts):

   ````bash
   ## Completed So Far
   - [checkpoint items]
   ## Remaining Work
   1. [next step]
   ## Key Context
   - [discoveries, constraints]
   ## Verification Commands
   ```bash
   [commands]
   ```

   ## Git Status

   ````

**Estimated boilerplate ratio by prompt type:**

| Prompt Type      | Boilerplate % | Unique Content % |
|------------------|---------------|------------------|
| Template (named) | 60-70%        | 30-40%           |
| Handoff          | 40-50%        | 50-60%           |
| Task             | 20-30%        | 70-80%           |
| Planning         | 15-25%        | 75-85%           |
| Audit            | 30-40%        | 60-70%           |
| Infrastructure   | 10-20%        | 80-90%           |

---

## 4. Common Patterns and Redundancy

### 4.1 Cross-Prompt Pattern Groups

#### Group A: Documentation & Audit Prompts

**Prompts:** 010, 012, 015, 016, 016.1–016.3 (juniper-ml); prompt45, prompt56 (named)

**Common elements:**

- Phase-based execution (Phase 0–6 typical)
- Cross-repo iteration pattern (repeat for each of 8 repos)
- Checklist-driven validation
- Output to `notes/` directory
- References to DOCUMENTATION_TEMPLATE_STANDARD.md

**Redundancy:** Prompts 010, 015, 016 overlap significantly in scope. Each re-specifies the 8-repo iteration list and documentation standards that could be centralized.

#### Group B: Docker / Deployment Prompts

**Prompts:** 019, 020, 021 (juniper-ml); 002, 003 (parent)

**Common elements:**

- Container configuration details
- Python version migration tracking
- Service port references (8100, 8200/8201, 8050)
- Docker Compose configuration validation
- Health endpoint verification (`/v1/health`)

**Redundancy:** Service ports, health endpoints, and Python version targets are repeated across all 5 prompts. These are facts derivable from `juniper-deploy` configuration.

#### Group C: CI/CD Pipeline Prompts

**Prompts:** prompt48, prompt56, prompt57, prompt58 (named)

**Common elements:**

- GitHub Actions workflow references
- Test runner configuration
- Coverage thresholds (80%)
- Pre-commit hook setup
- Linter configuration (black, isort, flake8/ruff)

**Redundancy:** CI configuration details (coverage targets, linter settings, Python versions) are repeated in each prompt and also exist in `pyproject.toml` files.

#### Group D: Thread Handoff Prompts

**Prompts:** 016, 016.1, 016.3 (juniper-ml); 008, 009 (parent)

**Common elements:**

- Identical section structure (Completed/Remaining/Context/Verification/Git Status)
- Branch and worktree references
- Verification bash commands
- Cross-references to procedures in `notes/`

**Redundancy:** The handoff structure is the most standardized and templatable of all prompt types. Only the content within each section varies.

#### Group E: Worktree & Git Management Prompts

**Prompts:** 003, 022, 023 (juniper-ml)

**Common elements:**

- Worktree path conventions
- Branch naming patterns
- Cleanup procedures
- Push-before-merge protocol

**Redundancy:** Worktree conventions are restated from CLAUDE.md and `notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`.

### 4.2 Redundancy Summary

| Redundancy Type                 | Instances   | Impact                    | Automation Potential       |
|---------------------------------|-------------|---------------------------|----------------------------|
| Role definition boilerplate     | 9+ prompts  | High (inconsistency risk) | **Template variable**      |
| Repo iteration list (8 repos)   | 6+ prompts  | Medium                    | **Environment discovery**  |
| Service port/endpoint table     | 5+ prompts  | Medium                    | **Config extraction**      |
| CI/CD configuration details     | 4+ prompts  | Medium                    | **pyproject.toml parsing** |
| Handoff section structure       | 5+ prompts  | Low (already consistent)  | **Template**               |
| Worktree naming convention      | 5+ prompts  | Low                       | **Reference link**         |
| Code change approval disclaimer | 10+ prompts | High (copy-paste drift)   | **Template include**       |
| Python version requirements     | 8+ prompts  | Medium                    | **Environment discovery**  |

### 4.3 Content Drift Observations

- Role definitions vary slightly across prompts (e.g., "helpful and experienced" vs. "knowledgeable and experienced")
- Code change approval disclaimer has minor wording variations between named prompts
- Handoff section headers have case inconsistency (`So Far` vs. `so far`)
- Repo lists occasionally omit newer repos (juniper-ml added later)

---

## 5. Natural Prompt Type Boundaries

Analysis reveals **6 natural prompt types** that differ in structure, purpose, and content composition:

### Type Classification Notes

**Compound prompts:** Some prompts span multiple types (e.g., an Audit prompt that includes Handoff sections, or a Planning prompt that transitions into Task execution). When classifying these, use a Primary/Secondary notation (e.g., "Audit+Handoff"). The type tables in Section 2.1 show the primary type only.

**Minimal prompts:** Very terse prompts (title + 1-2 sentences, no internal structure) blur the Infrastructure/Task boundary. When a prompt lacks sufficient structure for reliable classification, it defaults to its most likely type based on content rather than structure.

### Type 1: Thread Handoff Prompt

**Purpose:** Transfer work context between Claude Code threads
**Frequency:** ~15% of all prompts
**Distinguishing features:**

- Mandatory sections: Completed, Remaining, Key Context, Verification, Git Status
- No Role or Resources sections
- Content is entirely session-specific (no boilerplate)
- Always references a specific branch, worktree, and commit state

**Canonical structure:**

```markdown
# Thread Handoff: [Task Description]
---
## Completed So Far
## Remaining Work
## Key Context
## Verification Commands
## Git Status
```

### Type 2: Task Prompt

**Purpose:** Direct a specific implementation or fix task
**Frequency:** ~35% of all prompts
**Distinguishing features:**

- Action-oriented title
- Numbered steps or phases
- May include code blocks with examples
- Usually targets 1-3 repos
- Variable length (short for focused tasks, long for multi-phase work)

**Canonical structure:**

```markdown
# [Action Verb] [Subject]
## Overview
## [Task Sections with Numbered Steps]
## Requirements / Deliverables
```

### Type 3: Template Prompt (Named)

**Purpose:** Reusable task pattern for recurring work categories
**Frequency:** ~10% of prompts (12 named templates)
**Distinguishing features:**

- Descriptive UPPERCASE_SNAKE_CASE filename
- Full Role + Resources + Directives + Deliverables structure
- Explicit placeholders for customization
- Code change approval disclaimers
- Designed for reuse, not single sessions

**Canonical structure:**

```markdown
# [Category Title]
## Role
## Resources
## Primary Objective
## Assigned Tasks / Directives
## Key Deliverables and Requirements
```

### Type 4: Planning Prompt

**Purpose:** Design strategy, architecture, or migration plan
**Frequency:** ~15% of all prompts
**Distinguishing features:**

- Analysis-first approach
- Often produces output documents (plans, proposals, journals)
- References existing architecture and dependencies
- Usually cross-repo scope
- Includes evaluation criteria or design alternatives

**Canonical structure:**

```markdown
# [Subject] Plan / Analysis / Design
## Overview / Background
## Objectives
## [Analysis Sections]
## Deliverables
```

### Type 5: Audit Prompt

**Purpose:** Systematic review and validation of existing state
**Frequency:** ~12% of all prompts
**Distinguishing features:**

- Checklist-driven
- Phase-based execution (iterate across repos)
- Comparison against standards or templates
- Produces findings reports
- References validation criteria

**Canonical structure:**

```markdown
# [Subject] Audit
## Scope
## Audit Criteria / Standards
## Phase Plan (per-repo iteration)
## Deliverables
```

### Type 6: Infrastructure Prompt

**Purpose:** Configure tools, services, or development environment
**Frequency:** ~13% of all prompts
**Distinguishing features:**

- Operational focus (not code)
- Service-specific instructions
- Configuration values and credentials
- Verification-heavy
- Often one-time setup tasks

**Canonical structure:**

```markdown
# [Service/Tool] Setup / Configuration
## Goal
## Configuration Steps
## Verification
```

---

## 6. Automation Approaches

### 6.1 Approach A: Template Engine with Snippet Library

**Concept:** Create a library of Jinja2 (or similar) templates for each prompt type, with a snippet library for reusable boilerplate blocks. A CLI tool assembles prompts from templates + snippets + user-provided content.

**Architecture:**

```
prompts/
├── templates/              # Jinja2 templates per type
│   ├── handoff.md.j2
│   ├── task.md.j2
│   ├── template.md.j2
│   ├── planning.md.j2
│   ├── audit.md.j2
│   └── infrastructure.md.j2
├── snippets/               # Reusable content blocks
│   ├── role_senior_engineer.md
│   ├── role_integration_specialist.md
│   ├── resources_standard.md
│   ├── code_change_approval.md
│   ├── repo_list.md
│   └── service_ports.md
├── generated/              # Output directory
└── config/
    └── prompt_defaults.yaml  # Default values for template variables
```

**How it works:**

1. User selects a prompt type
2. Tool loads the corresponding template
3. User provides type-specific content (title, tasks, target repos)
4. Tool injects snippets and defaults
5. Output is a complete, ready-to-use prompt markdown file

**Strengths:**

- Eliminates boilerplate drift
- Single source of truth for reusable blocks
- Easy to add new types
- Familiar technology (Jinja2, YAML)
- Templates are readable and auditable
- Version-controllable

**Weaknesses:**

- Requires learning template syntax for modifications
- Template complexity can grow over time
- Snippets may become stale if project changes
- Manual trigger required (not automatic)

**Risk level:** Low
**Implementation effort:** Medium (2-3 days)

---

### 6.2 Approach B: Database-Backed Prompt Composition

**Concept:** Store prompt components (metadata, sections, snippets, project context) in a structured data store (SQLite, JSON, or YAML). A builder script queries the database and assembles prompts.

**Architecture:**

```
prompts/
├── db/
│   ├── prompt_registry.yaml     # All prompt metadata (type, target, date, status)
│   ├── sections.yaml            # Section content keyed by ID
│   ├── snippets.yaml            # Reusable text blocks
│   ├── projects.yaml            # Project metadata (repos, ports, versions)
│   └── schema.yaml              # Validation schema
├── scripts/
│   └── prompt_builder.py        # Assembly + validation tool
└── generated/
```

**Data model (prompt_registry.yaml):**

```yaml
prompts:
  - id: "024"
    type: task
    title: "Add health check monitoring"
    date: "2026-03-12"
    targets: [juniper-cascor, juniper-canopy]
    sections:
      - overview: "inline content or ref:sections/overview_024"
      - tasks: "ref:sections/tasks_024"
    snippets: [role_senior_engineer, resources_standard, code_change_approval]
    status: active
```

**Strengths:**

- Structured metadata enables querying and reporting
- Central registry prevents duplicate/overlapping prompts
- Project metadata (ports, versions) is single-sourced
- Supports search: "show all audit prompts for juniper-cascor"
- Enables dependency tracking between prompts

**Weaknesses:**

- Higher complexity than templates alone
- YAML/JSON can become unwieldy at scale
- Requires tooling to compose and validate
- Harder to hand-edit than plain markdown
- Overkill for the current corpus size (~131 files)

**Risk level:** Medium
**Implementation effort:** High (4-6 days)

---

### 6.3 Approach C: Environment Discovery Scripts

**Concept:** Utility scripts that introspect the Juniper ecosystem at runtime and inject discovered facts into prompts. Eliminates hardcoded values (repo lists, ports, versions, branches, worktree status).

**Components:**

```
scripts/
├── discover_repos.bash         # List all Juniper repos with metadata
├── discover_services.bash      # Extract ports, health endpoints from Docker config
├── discover_environment.bash   # Python versions, conda envs, active branches
├── discover_worktrees.bash     # Active worktrees, branches, status
├── discover_ci.bash            # CI/CD config, coverage thresholds, linter settings
└── discover_all.bash           # Aggregate all discovery into JSON/YAML
```

**Output format (JSON):**

```json
{
  "repos": [
    {
      "name": "juniper-cascor",
      "path": "/home/pcalnon/Development/python/Juniper/juniper-cascor",
      "branch": "main",
      "python_version": ">=3.11",
      "conda_env": "JuniperCascor",
      "has_agents_md": true,
      "ci_coverage_threshold": 80
    }
  ],
  "services": [
    {"name": "juniper-data", "port": 8100, "health": "/v1/health"}
  ],
  "worktrees": [
    {"repo": "juniper-ml", "branch": "tooling/more_claude_utils", "path": "..."}
  ],
  "environment": {
    "platform": "linux",
    "python_default": "3.14",
    "conda_prefix": "/opt/miniforge3"
  }
}
```

**Strengths:**

- Always up-to-date (discovers current state, not cached values)
- Eliminates the most common redundancy source (hardcoded facts)
- Composable with any template approach
- Independently useful for other tooling
- Simple to implement (bash + jq)

**Weaknesses:**

- Runtime dependency (must execute before prompt creation)
- May be slow if introspecting many repos
- Cannot discover "soft" information (project goals, task context)
- Requires maintained discovery scripts
- Platform-specific (Linux/macOS)

**Risk level:** Low
**Implementation effort:** Medium (2-3 days)

---

### 6.4 Approach D: Interactive Prompt Builder CLI

**Concept:** An interactive CLI tool (extending `wake_the_claude.bash`) that guides users through prompt creation with menus, defaults, and validation.

**User flow:**

```
$ ./scripts/create_prompt.bash

Juniper Prompt Builder v1.0
===========================
1. Select prompt type:
   [1] Thread Handoff
   [2] Task
   [3] Template (Named)
   [4] Planning
   [5] Audit
   [6] Infrastructure

> 2

2. Target project(s) (comma-separated, or 'all'):
> juniper-cascor, juniper-deploy

3. Prompt title:
> Fix Docker health check timing

4. Include sections:
   [x] Overview
   [x] Tasks (numbered)
   [ ] Role definition
   [ ] Resources
   [x] Verification commands
   [ ] Code change approval

5. Include environment discovery? [Y/n]: Y

Generating prompt... Done!
Saved: prompts/prompt024_2026-03-12.md
```

**Strengths:**

- Lowest barrier to entry (guided experience)
- Enforces naming conventions automatically
- Can integrate environment discovery
- Validates structure against type requirements
- Auto-numbers prompts sequentially

**Weaknesses:**

- Interactive mode requires terminal (not scriptable without flags)
- Must support both interactive and non-interactive modes
- More complex to maintain than simple templates
- May be over-prescriptive for creative prompts
- Requires bash proficiency to extend

**Risk level:** Medium
**Implementation effort:** High (4-5 days)

---

### 6.5 Approach E: Hybrid Template + Discovery + Metadata

**Concept:** Combine the best elements of Approaches A, C, and a lightweight metadata index. Templates define structure, discovery scripts inject facts, and a YAML index tracks all prompts.

**Architecture:**

```
prompts/
├── templates/                    # Jinja2 templates per prompt type
│   ├── base.md.j2               # Common base template
│   ├── handoff.md.j2
│   ├── task.md.j2
│   ├── audit.md.j2
│   └── ...
├── snippets/                    # Reusable content blocks
│   ├── roles/
│   ├── resources/
│   └── disclaimers/
├── index.yaml                   # Prompt metadata registry
├── active/                      # Current session prompts
└── archive/                     # Historical prompts (by month)

scripts/
├── prompt_create.bash           # Create prompt from template + discovery
├── prompt_archive.bash          # Archive old prompts
├── discover_env.bash            # Environment introspection
└── prompt_validate.bash         # Validate prompt structure against type schema
```

**Workflow:**

1. `prompt_create.bash --type task --target juniper-cascor --title "Fix tests"`
2. Script runs `discover_env.bash` to gather current state
3. Loads `templates/task.md.j2` and `snippets/` as needed
4. Renders prompt with discovered data + user input
5. Appends entry to `index.yaml`
6. Saves to `active/prompt024_2026-03-12.md`

**Strengths:**

- Best of all approaches: templates for structure, discovery for facts, index for tracking
- Modular and incrementally adoptable
- Each component is independently useful
- Transparent (all artifacts are readable markdown/YAML)
- Supports both CLI and manual editing
- Natural extension of existing `wake_the_claude.bash`

**Weaknesses:**

- More moving parts than any single approach
- Requires maintenance across templates, snippets, and discovery scripts
- Initial setup time is highest
- Over-engineered if prompt volume remains low

**Risk level:** Medium
**Implementation effort:** High (5-7 days)

---

### 6.6 Approach F: Convention-Only (No Tooling)

**Concept:** Define a style guide and naming convention for prompts. No automation tooling — just documented standards that humans follow.

**Artifacts:**

- `notes/PROMPT_STYLE_GUIDE.md` — Section requirements per type, naming rules, boilerplate blocks to copy
- `prompts/templates/` — Markdown template files (copy-and-fill, not rendered)

**Strengths:**

- Zero implementation effort
- No dependencies
- Maximum flexibility
- Easy to understand

**Weaknesses:**

- Relies entirely on human discipline
- Boilerplate drift will continue
- No validation
- No environment discovery
- Inconsistency is inevitable over time

**Risk level:** Low
**Implementation effort:** Low (0.5-1 day)

---

## 7. Implementation Details

### 7.1 Template System (Approaches A/E)

**Technology choice: Jinja2 via Python**

Jinja2 is the recommended template engine because:

- Already available in the Python ecosystem (all Juniper projects use Python)
- Supports template inheritance (`{% extends "base.md.j2" %}`)
- Supports includes (`{% include "snippets/role.md" %}`)
- Supports conditionals (`{% if include_role %}`)
- Well-documented and widely understood

**Example template (`templates/task.md.j2`):**

```jinja2
{% extends "base.md.j2" %}

{% block title %}# {{ title }}{% endblock %}

{% block body %}
## Overview

{{ overview }}

{% if include_role %}
{% include "snippets/roles/" + role_variant + ".md" %}
{% endif %}

{% if targets %}
## Target Projects

| Project | Conda Env | Python | Port |
|---------|-----------|--------|------|
{% for t in targets %}
| {{ t.name }} | {{ t.conda_env | default('-') }} | {{ t.python_version }} | {{ t.port | default('-') }} |
{% endfor %}
{% endif %}

## Tasks

{% for task in tasks %}
### {{ loop.index }}. {{ task.title }}

{{ task.description }}

{% endfor %}

{% if include_verification %}
## Verification Commands

```bash
{% for cmd in verification_commands %}
{{ cmd }}
{% endfor %}
```

{% endif %}

{% if include_approval_disclaimer %}
{% include "snippets/disclaimers/code_change_approval.md" %}
{% endif %}
{% endblock %}

```

**Example snippet (`snippets/roles/senior_engineer.md`):**
```markdown
## Role

- You are a helpful and experienced Software Engineer with extensive experience in Machine Learning and Artificial Intelligence.
- You approach problems logically and systematically, breaking them down into smaller, more manageable parts.
- You develop a plan prior to starting any task, ensuring that you have a clear understanding of the problem and the steps required to solve it.
```

### 7.2 Environment Discovery (Approach C)

**Implementation: Bash + jq**

**Core discovery script (`scripts/discover_env.bash`):**

```bash
#!/usr/bin/env bash
# Discover Juniper ecosystem state and output JSON

JUNIPER_ROOT="/home/pcalnon/Development/python/Juniper"
REPOS=(juniper-cascor juniper-data juniper-data-client juniper-cascor-client
       juniper-cascor-worker juniper-ml juniper-canopy juniper-deploy)

discover_repos() {
    for repo in "${REPOS[@]}"; do
        local path="$JUNIPER_ROOT/$repo"
        [[ -d "$path/.git" ]] || continue
        local branch=$(git -C "$path" branch --show-current 2>/dev/null)
        local python_ver=$(grep -oP 'python_requires\s*=\s*">=\K[^"]+' \
            "$path/pyproject.toml" 2>/dev/null || echo "unknown")
        echo "{\"name\":\"$repo\",\"branch\":\"$branch\",\"python\":\"$python_ver\"}"
    done | jq -s '.'
}

discover_services() {
    local compose="$JUNIPER_ROOT/juniper-deploy/docker-compose.yml"
    # Parse service ports from docker-compose
    # Output structured JSON
}

discover_worktrees() {
    local wt_dir="$JUNIPER_ROOT/worktrees"
    [[ -d "$wt_dir" ]] || { echo "[]"; return; }
    for d in "$wt_dir"/*/; do
        local name=$(basename "$d")
        echo "{\"name\":\"$name\",\"path\":\"$d\"}"
    done | jq -s '.'
}

# Main output
jq -n \
    --argjson repos "$(discover_repos)" \
    --argjson services "$(discover_services)" \
    --argjson worktrees "$(discover_worktrees)" \
    '{repos: $repos, services: $services, worktrees: $worktrees,
      timestamp: now | strftime("%Y-%m-%dT%H:%M:%S")}'
```

### 7.3 Prompt Index (Approach B/E)

**Implementation: YAML file**

**Example (`prompts/index.yaml`):**

```yaml
# Juniper Prompt Index
# Auto-maintained by prompt_create.bash
# Manual edits are allowed

prompts:
  - id: "024"
    type: task
    title: "Fix Docker health check timing"
    date: "2026-03-12"
    location: "juniper-ml/prompts/prompt024_2026-03-12.md"
    targets: [juniper-cascor, juniper-deploy]
    status: active  # active | archived | superseded
    superseded_by: null
    tags: [docker, health-check, deployment]

  - id: "023"
    type: task
    title: "Cleanup continuation"
    date: "2026-03-11"
    location: "juniper-ml/prompts/prompt023_2026-03-11.md"
    targets: [juniper-ml, juniper-data-client]
    status: archived
    tags: [worktree, cleanup]
```

### 7.4 Integration with wake_the_claude.bash

The existing `wake_the_claude.bash` already supports:

- `-f/--file` for prompt file selection
- `-l/--path` for prompt directory
- `-p/--prompt` for inline prompt text
- Session ID persistence
- Resume capabilities

**Proposed extensions:**

1. Add `--type` flag to trigger template-based generation
2. Add `--discover` flag to run environment discovery before launch
3. Add `--list` flag to display prompt index
4. Add `--archive` flag to move prompts to history directories

### 7.5 Handoff Prompt Auto-Generation

Thread handoff prompts are the most formulaic and automatable type. A specialized tool could:

1. Introspect the current git state (branch, diff, log)
2. Accept user-provided "completed" and "remaining" items
3. Auto-populate verification commands based on discovered state
4. Format the output using the standardized handoff template
5. Save with proper naming convention

**Script:** `scripts/create_handoff.bash`

```bash
#!/usr/bin/env bash
# Generate a thread handoff prompt from current git state

BRANCH=$(git branch --show-current)
WORKTREE=$(pwd)
LAST_COMMITS=$(git log --oneline -5)
MODIFIED_FILES=$(git diff --name-only HEAD~3)

# Interactive prompts for completed/remaining sections
read -p "Task description: " TASK_DESC
echo "Enter completed items (one per line, empty line to stop):"
# ... collect input ...

# Render template
envsubst < templates/handoff.md.j2 > "prompts/prompt${NEXT_NUM}_$(date +%Y-%m-%d).md"
```

---

## 8. Risk Analysis and Guardrails

### 8.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Template drift** — Templates become stale as project evolves | Medium | Medium | Periodic review; discovery scripts reduce hardcoded values |
| **Over-templating** — Creativity constrained by rigid templates | Medium | Low | Templates are optional; manual creation always possible |
| **Tooling fragility** — Scripts break with ecosystem changes | Medium | Medium | Integration tests; minimal dependencies (bash + jq + Python) |
| **Adoption friction** — Tool is harder than manual creation | Low | High | Keep CLI simple; support both interactive and non-interactive modes |
| **Index staleness** — YAML index falls out of sync with files | Medium | Low | Validation script; auto-update on create/archive |
| **Discovery errors** — Scripts produce incorrect data | Low | Medium | Unit tests for discovery scripts; human review of generated prompts |
| **Complexity creep** — System grows beyond maintainability | Medium | High | Set scope limits; document "this is intentionally not supported" |
| **Lock-in** — Generated prompts are unusable without tooling | Very Low | High | Output is plain markdown; tooling is optional convenience layer |

### 8.2 Guardrails

1. **Output is always plain markdown.** No proprietary formats. Generated prompts must be human-readable and editable without any tooling.

2. **Manual creation is always supported.** The automation is a convenience layer, not a gate. Users can always create prompts by hand following the style guide.

3. **Templates are transparent.** Jinja2 templates are readable markdown with minimal logic. No complex inheritance chains deeper than 2 levels.

4. **Discovery is optional.** Prompts can be created without running discovery scripts. Templates should have sensible defaults and allow manual override.

5. **Index is advisory.** The YAML index is a convenience for search and tracking. It does not gate prompt creation or use.

6. **No destructive operations.** Archiving moves files, never deletes. Old prompts are always preserved.

7. **Version control is the source of truth.** All templates, snippets, scripts, and generated prompts are committed to git.

---

## 9. Approach Comparison Matrix

### 9.1 Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Transparency** | High | Can a new contributor understand the system? |
| **Maintainability** | High | How much ongoing effort to keep the system healthy? |
| **Flexibility** | High | Can it handle novel prompt types or structures? |
| **Repeatability** | Medium | Does it produce consistent results? |
| **Implementation effort** | Medium | Time to build and integrate |
| **Adoption barrier** | Medium | How easy is it for users to start using? |
| **Risk** | Medium | What can go wrong? |

### 9.2 Comparative Scores

| Criterion | A: Templates | B: Database | C: Discovery | D: CLI Builder | E: Hybrid | F: Convention |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Transparency | 9 | 6 | 9 | 7 | 8 | 10 |
| Maintainability | 8 | 5 | 7 | 6 | 7 | 4 |
| Flexibility | 7 | 8 | 6 | 7 | 9 | 10 |
| Repeatability | 9 | 9 | 8 | 9 | 9 | 3 |
| Impl. effort | 7 | 4 | 8 | 5 | 4 | 10 |
| Adoption barrier | 7 | 5 | 8 | 8 | 7 | 9 |
| Risk (lower=better) | 8 | 5 | 8 | 6 | 6 | 9 |
| **Weighted Total** | **7.9** | **6.0** | **7.7** | **6.9** | **7.1** | **7.9** |

### 9.3 Approach Ranking

| Rank | Approach | Score | Best For |
|------|----------|-------|----------|
| 1 (tie) | **A: Template Engine** | 7.9 | Teams wanting structured output with low overhead |
| 1 (tie) | **F: Convention-Only** | 7.9 | Small teams with discipline; immediate adoption |
| 3 | **C: Discovery Scripts** | 7.7 | Eliminating hardcoded facts; composable with any approach |
| 4 | **E: Hybrid** | 7.1 | Full automation with all features; larger teams |
| 5 | **D: CLI Builder** | 6.9 | Users who prefer guided experiences |
| 6 | **B: Database-Backed** | 6.0 | Large prompt libraries needing queryability |

---

## 10. Recommendations

### 10.1 Recommended Strategy: Phased Adoption

Given the current ecosystem size, team composition, and existing infrastructure, the recommended strategy is a **phased approach** starting simple and adding complexity only as needed.

#### Phase 1: Foundation (Immediate — 1 day)

**Goal:** Establish conventions and eliminate the most impactful redundancies.

**Actions:**

1. **Create a prompt style guide** (`notes/PROMPT_STYLE_GUIDE.md`) documenting:
   - The 6 prompt types and their required sections
   - Naming conventions (already established)
   - Boilerplate blocks to copy
   - Archive procedures

2. **Extract boilerplate into snippet files** (`prompts/snippets/`):
   - `role_senior_engineer.md`
   - `role_integration_specialist.md`
   - `resources_standard.md`
   - `code_change_approval.md`

3. **Create markdown template files** (`prompts/templates/`):
   - One per prompt type (6 files)
   - Copy-and-fill format (no rendering engine needed)
   - Comments indicating which sections are required vs. optional

**Rationale:** This delivers immediate value with near-zero risk. Templates and snippets are just markdown files — no tooling required.

#### Phase 2: Discovery (Week 1 — 2 days)

**Goal:** Automate environment introspection to eliminate hardcoded values.

**Actions:**

1. **Implement `discover_env.bash`** — outputs JSON with repo metadata, service ports, Python versions, conda envs, active worktrees
2. **Integrate with `wake_the_claude.bash`** — add `--discover` flag
3. **Create snippet generation** — script that reads discovery output and produces up-to-date markdown snippets (repo table, service table, etc.)

**Rationale:** Discovery scripts have the highest return-on-investment. They eliminate the most common source of redundancy (hardcoded ecosystem facts) and are useful beyond prompt creation.

#### Phase 3: Template Rendering (Week 2 — 2-3 days)

**Goal:** Automated prompt composition from templates + discovery data.

**Actions:**

1. **Implement `prompt_create.bash`** — CLI tool with flags:
   - `--type {handoff|task|template|planning|audit|infrastructure}`
   - `--title "prompt title"`
   - `--target repo1,repo2`
   - `--discover` (auto-inject environment data)
   - `--snippets role,resources,approval` (include specific snippets)
2. **Add Jinja2 rendering** via a small Python helper (or use `envsubst` for simpler cases)
3. **Auto-number prompts** based on existing files in the target directory

**Rationale:** Building on Phase 1 snippets and Phase 2 discovery, template rendering adds the composition layer that makes prompt creation fast and consistent.

#### Phase 4: Tracking (Week 3 — 1 day)

**Goal:** Prompt metadata index for search and lifecycle management.

**Actions:**

1. **Create `prompts/index.yaml`** — lightweight registry of all prompts with type, target, date, status, tags
2. **Add `prompt_archive.bash`** — move prompts to history directories and update index
3. **Add `prompt_search.bash`** — query the index by type, target, date, or tags
4. **Backfill index** with existing 131+ prompts (scripted extraction from filenames)

**Rationale:** The index is low-effort and enables operational questions like "what prompts have we run against juniper-cascor?" or "which prompts are still active?"

#### Phase 5: Handoff Automation (Week 4 — 1 day)

**Goal:** Specialized tool for the most common and formulaic prompt type.

**Actions:**

1. **Implement `create_handoff.bash`** — auto-generates handoff prompts from git state
2. **Integrate with thread handoff procedure** — can be triggered when approaching context limits
3. **Auto-populate:** branch, recent commits, modified files, worktree path, verification commands

**Rationale:** Handoff prompts are the most templatable type and benefit most from automation because they're time-sensitive (created under context pressure).

### 10.2 What NOT to Build

- **No database backend.** YAML + filesystem is sufficient for the current scale (~10-20 prompts/month).
- **No web UI.** CLI tools integrated with `wake_the_claude.bash` are the right interface.
- **No AI-generated prompt content.** Templates should produce structure; humans provide the task-specific content.
- **No mandatory tooling.** Manual prompt creation must always remain supported.

### 10.3 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Boilerplate consistency | 100% identical across prompts using same snippets | Diff comparison |
| Prompt creation time | < 2 minutes for templated types | User self-report |
| Handoff prompt completeness | 100% include all required sections | Validation script |
| Discovery accuracy | 100% match with actual ecosystem state | Cross-check with git/docker |
| Adoption rate | > 80% of new prompts use templates | Index analysis |

### 10.4 Maintenance Plan

| Activity | Frequency | Owner |
|----------|-----------|-------|
| Update snippets when boilerplate changes | As needed | Prompt author |
| Update discovery scripts when repos/services change | Per change | Developer |
| Archive completed prompts | Monthly | Developer |
| Review prompt index for staleness | Monthly | Developer |
| Update templates for new prompt patterns | Quarterly | Developer |

---

## 11. Appendices

### Appendix A: File Reference

| Path | Purpose |
|------|---------|
| `juniper-ml/prompts/` | Active session prompts (numbered) |
| `Juniper/prompts/` | Cross-project prompts (top-level + archives) |
| `Juniper/prompts/history-*/` | Archived historical prompts |
| `Juniper/prompts/history-named-prompts_*/` | Reusable task template prompts |
| `juniper-ml/scripts/wake_the_claude.bash` | Claude Code launcher with session management |
| `juniper-ml/scripts/sessions/` | Session ID persistence directory |
| `juniper-ml/notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` | Handoff protocol specification |
| `juniper-ml/notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md` | Worktree creation procedure |

### Appendix B: Prompt Type Decision Tree

```
Is this transferring work between threads?
├─ Yes → Type 1: HANDOFF
└─ No → Does it define a reusable task pattern?
    ├─ Yes → Type 3: TEMPLATE
    └─ No → Is the primary goal to review/validate existing state?
        ├─ Yes → Type 5: AUDIT
        └─ No → Is the primary goal to design strategy or architecture?
            ├─ Yes → Type 4: PLANNING
            └─ No → Is it configuring tools/services (not code)?
                ├─ Yes → Type 6: INFRASTRUCTURE
                └─ No → Type 2: TASK
```

### Appendix C: Named Prompt Category Mapping

| Named Prompt | Prompt Type | Reuse Pattern |
|-------------|-------------|---------------|
| AGENTS_FILE_CREATION | Template (Implementation) | Per-repo documentation generation |
| INTEGRATION_ROADMAP | Template (Planning) | Cross-repo integration planning |
| PERFORM_CODE_REVIEW | Template (Audit) | Pre-deployment review |
| TEST_PERFORMANCE_IMPROVEMENT | Template (Task) | Test optimization |
| DOCUMENTATION_AUDIT | Template (Audit) | Documentation quality review |
| EXTRACT_OBJECT_REFACTOR | Template (Planning) | Refactoring design |
| DOCMENTATION_CREATION | Template (Task) | Documentation generation |
| TEST_CICD_CREATE_PIPELINE | Template (Task) | CI/CD pipeline setup |
| TEST_COVERAGE_INCREASE | Template (Task) | Test coverage improvement |
| TEST_CICD_FULL_AUDIT | Template (Audit) | CI/CD audit |
| TEST_CICD_UPGRADE_PLAN | Template (Planning) | CI/CD enhancement design |
| TEST_CICD_IMPLEMENT_UPGRADE_PLAN | Template (Task) | CI/CD enhancement implementation |

### Appendix D: Existing Infrastructure Summary

| Component | Location | Capabilities |
|-----------|----------|-------------|
| `wake_the_claude.bash` | `scripts/` | Session management, prompt file loading, ~53 flag aliases (21 named variables), interactive/headless modes |
| Session persistence | `scripts/sessions/` | UUID-based session files, resume support |
| `default_interactive_session_claude_code.bash` | `scripts/` | Default session wrapper |
| `test.bash` | `scripts/` | End-to-end launcher testing |
| `test_resume_file_safety.bash` | `scripts/` | Regression test for file safety |
| `tests/test_wake_the_claude.py` | `tests/` | Unit tests for session/argument handling |

---

### Appendix E: Validation Summary

This plan was validated by three independent sub-agents on 2026-03-12:

**1. File Reference Validation** — All file/directory references verified against filesystem.

- Result: **PASS**. All existing files confirmed; all proposed files correctly marked as to-be-created.
- Correction applied: Added missing `history-named-prompts_2026-02-06/` archive directory.

**2. Type Classification Validation** — 12-prompt sample verified against 6-type system.

- Result: **PASS with corrections**. 8/12 correct (67%), 1 misclassification fixed (prompt016: Handoff→Planning), 2 too sparse to verify.
- Enhancement applied: Added compound type notation support (Primary+Secondary).

**3. Automation Feasibility Validation** — Infrastructure claims and data sources verified.

- Result: **PASS**. All discovery data sources confirmed (pyproject.toml, docker-compose.yml, conda envs, worktrees). No flag conflicts with proposed extensions.
- Corrections applied: Updated flag count (23+ → ~53 aliases), refined boilerplate percentage to be type-specific.

| Validation Area | Result | Corrections Applied |
|----------------|--------|-------------------|
| File references | PASS | Added missing archive directory |
| Type classification | PASS (with fixes) | Fixed prompt016 type; added compound type support |
| Infrastructure claims | PASS | Updated flag count; refined boilerplate estimates |
| Discovery feasibility | PASS | All data sources verified |
| Flag conflicts | PASS | No conflicts detected |
| Overall plan validity | **85-90% accuracy** | All corrections incorporated |

---

*Document generated 2026-03-12. This plan should be reviewed and updated as the Juniper prompt ecosystem evolves.*
