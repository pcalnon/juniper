# HANDOFF — post-flood / post-sequence-safety STANDING ITEMS (juniper-ml + ecosystem)

Continue the **standing-items arc** left after the two now-complete programs:
Cursor-PR-flood remediation and the sequence-safety ecosystem rollout. Grounded live against
`origin/main` on 2026-08-08. Records:
`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`,
`notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`,
`notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md`.

## Completed so far (verified)

- Flood remediation shipped: `merge_group` triggers + per-SHA main concurrency (**ml#869**, 2026-07-30);
  `strict_required_status_checks_policy=true` on ruleset **13805432** (13 required contexts);
  `.github/workflows/pr-budget-alarm.yml`; fleet-supervisor Stage-0
  (`.claude/agents/fleet-supervisor.md` + `util/fleet_triage/predict_merge.py` +
  `tests/test_predict_merge.py` + `tests/test_fleet_supervisor_contract.py`); bypass-actor research
  (**ml#925** merged the doc).
- Sequence-safety rollout **fleet-complete**: screens packaged in `juniper-ci-tools` **0.8.0**
  (Waves 0/1); all seven non-ml repos carry `sequence-safety.yml` + `main-verify.yml`
  (Wave 2 + cascor#482); ml retrofit consumes the package and deleted `util/sequence_safety/`
  (Wave 3, **#1024**); precondition polish **ml#1004** merged 2026-08-08.
- Resolved standing candidates (dropped): canopy v0.6.0 notes design-links pinned to owning-repo URLs
  (**ml#1003**, 2026-08-08 04:19Z); cascor storm follow-ups **cascor#471** (MERGED 08-08) and
  **cascor#477** (MERGED 08-07).

## Remaining work (standing items — each probed 2026-08-08)

1. **Sequence-safety promotion to required contexts** — per-repo owner call *after soak* (plan D8).
   Soak is fresh: cascor 47 runs (46 success / 1 cancelled) since 08-07; the six consumers 1-2 runs
   each, all success, all 08-08; ml runs it as a `ci.yml` job. Recommendation (promote after a storm
   survives OR ~2 weeks clean) **not yet met** → keep advisory, track soak; do not promote yet.
2. **#925 bypass-cleanup agenda — 5 owner decisions, all UNEXECUTED** (ruleset 13805432 bypass list is
   byte-for-byte unchanged since the 08-05 research: 5 `always` + 1 `pull_request`). (a) identify
   Integration **1276151** (owner UI; also always-bypass on cascor ruleset 15081045); (b) audit the two
   writable DeployKeys incl. the 2026-08-03-active one; (c) remove cursor **1210556** + claude
   **1236702** `always` bypasses — KEEP owner RepositoryRole 5 and the release-train App **4362741**
   (`pull_request`); (d) fix the `code_quality`-no-reporting-tool deadlock (attach a tool or drop the
   rule — the reason 4362741 exists); (e) merge-queue↔bypass coupling.
3. **Merge-queue availability + rule** — no `merge_queue` rule present; `strict=true` fallback already
   live; `merge_group` prereq already wired. Verify UI availability first (owner notes a
   `merge_queue`-422-on-personal-repos report → may be plan-gated), then add the rule *and* remove the
   app bypasses (2c) so it binds fleet PRs; it never binds owner batch-merges (Role 5).
4. **Fleet-supervisor next-storm readiness** — Stage-0 operational. First move on any storm =
   `predict_merge --batch` triage BEFORE any merges. The two wave-2 PR follow-ups are resolved
   (cascor#471/#477, both MERGED); next storm ~early September (cadence inference — flag as inference).
5. **Release-train Phase-5 trackers** (plan §12): 5.1 **Q-META** (meta-package stays manual; revisit)
   and 5.2 **Q-NONSHIP** (skip remains default; hygiene-sweep toggle considered later). Low-urgency
   deferred reevaluations, not urgent work.
6. **codeql.yml template divergence** — ml's `codeql.yml` gained `merge_group` (ml#869) while the
   fleet template source `juniper-data/.github/workflows/codeql.yml` still lacks it. Either propagate
   `merge_group` to the template + siblings or record accepted divergence (latent until a queue exists
   in a given repo).

## Key context / doctrine (carry forward)

- **Ground against `origin/main`** — any pre-existing worktree HEAD is a stale (clean) ancestor of
  `origin/main` (main advances multiple times per hour during active periods). Fetch first; pin your
  own grounding SHA at session start.
- Squash-merge commits carry `Allow-*` waiver trailers; **never reproduce a full `Allow-*` trailer or
  the CI-skip marker verbatim** in any commit message or PR body (load-bearing tokens).
- Use a **per-agent scratchpad subdir** for temp files.
- All 8 repos enforce `required_signatures` on main → headless PR-branch work uses GitHub-signed API
  commits (`createCommitOnBranch`), never a plain unsigned `git push`.
- **Never run the release-train live seam** (`ceremony.py` / `propose.py --execute`) from a shared
  clone of a worktree.
- `gh pr list` **dup-guard** before opening any PR (concurrent Cursor sessions run).
- **Owner-only** pypi / environment gates; headless merges only within Paul's explicit approval scope.
  **Derive the open-PR set LIVE (`gh pr list` per repo) — never trust a snapshot**, including this
  one: PR states churned twice during this handoff's own validation pass. At draft time the known
  owner-gated release-train proposals were ml **#1026** / ml **#1028** (leave them — NOT session work);
  any open feature PR belongs to a concurrent session — dup-guard against it, never touch its branch.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin
python util/prompt_discovery/cli.py --repo-root "$(pwd)"                      # grounding bundle
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.bypass_actors, ([.rules[].type])'
gh run list --repo pcalnon/juniper-cascor --workflow sequence-safety.yml -L 60 \
  --json conclusion,createdAt   # soak counter (repeat per consumer repo)
gh pr list --repo pcalnon/juniper-ml --state open --json number,title,headRefName
```

Expected git state: `main` clean and current. Derive the open-PR set live with the last command
above and classify each (owner-gated proposal / concurrent-session feature work / fleet) before
acting. Start fresh from `origin/main` — do not resume any prior session's worktree branch.
