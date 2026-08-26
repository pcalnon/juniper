# HANDOFF — P5 continuation: verification, promotion-readiness facts, both 08-25 handoffs validated, `--ref` restored, preconditions 2–4 recorded

**Date**: 2026-08-26
**Origin session**: `p5 ports, session split [3c9662]` (worktree `idempotent-dreaming-panda`)
**Predecessors**: [`HANDOFF_2026-08-25_p5-ports-and-session-split.md`](HANDOFF_2026-08-25_p5-ports-and-session-split.md)
(ml#1380) and its sibling [`HANDOFF_2026-08-25_p5-four-ports-and-helper-fold.md`](HANDOFF_2026-08-25_p5-four-ports-and-helper-fold.md)
(ml#1384) — both now carry a Validation section (ml#1395).

**Validation status**: self-reviewed; every figure below is a live probe from this session, none
inherited (the peer's eight precondition figures were re-probed from GitHub before use). A four-lens
pass over THIS document is owed to the next session — run the lenses **sequentially in one session**
(see Key context: eight parallel refuting agents died on the API session limit before reporting).

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** arc in `juniper-ml`, P5 fleet rollout. Authorities: plan §P5
in [`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md)
(banner, steps b/d and the precondition record are current as of this handoff's PR; the measurement
paragraph by ml#1398); tracker **ml#1326** (its comments are the live ledger — newest first).

**Dup-guard before any work**: `ListAgents`, then message any session named `memory budget` with
what you intend to take; `gh pr list --state all` on ml and each target; the tracker's newest
comments. Two sessions duplicated each other on 08-25 from ONE handoff.

### State (2026-08-26 ~14:50 CDT)

- All 8 ports MERGED (canopy#516, cascor#585, cascor-client#139, recurrence#131, data-client#173,
  data#291, cascor-worker#162, deploy#195); ml#1376/#1379/#1380/#1384 MERGED; **ml#1395 MERGED**
  18:02Z (`d038258f`); **ml#1398 MERGED** 19:43Z (`d95759f8`, `measure-growth --ref` restored, 26
  tests). slacker has no `AGENTS.md`.
- **Preconditions 2–4 shipped by the peer session `memory budget`** (one signed PR per repo on
  `feat/memory-budget-blocking`: `--advisory` removed, three controls re-run non-advisory,
  `Allow-Ceiling-Raise: AGENTS.md` = max(largest 30-day growing commit, 2,000 fan-out floor)).
  **All eight MERGED**: deploy#196 `1fe58592` 34,569→36,569 · recurrence#132 `a80a7dc9` 11,578→13,698 ·
  cascor-worker#163 `cf5ae76d` 35,126→37,126 · cascor-client#140 `87464c35` 34,695→37,277 ·
  data#294 `e0b738e6` 43,493→45,493 · cascor#591 `c6cd2f09` 71,098→80,707 · data-client#174
  `a3226826` 28,369→30,442 · canopy#529 `9f6fac97` 95,133→97,133 (19:34Z, after two re-syncs).
  Ceilings on each `main` and the checker's invocation lines re-probed from GitHub: they match.
  `Memory Budget` = SUCCESS on every PR head via the non-advisory job (`[RAISE-WAIVED] … headroom=`).
- **NONE promoted.** The ruleset `--apply` is the owner's call, per repo. `--status --context
  'Memory Budget'` reports observed YES on all 8.
- No arc worktree remains; the juniper-ml primary is at `origin/main` (re-check after each merge).

### Remaining work

1. **The plan banner is current as of this PR** (all 8 BLOCKING, none promoted). §4a: status may
   not be left stale — the next state change is a promotion, and only the owner makes it.
2. **Promotion (owner-gated)**: for all eight, all four preconditions hold; the write is
   `python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-<x> --context 'Memory Budget'`
   (dry-run) then `--apply`, one repo at a time, only on the owner's explicit go. `main` shows the
   job as `skipped` by design — never pass `--allow-unobserved` for that reason. Pass `--repo` for
   juniper-recurrence (not in the default roster).
3. **The peer lineage's artifacts are theirs — do not duplicate**: archive PR ml#1400 (handoff +
   `util/ad-hoc/2026-08-26_p5_fleet_state.py` and `2026-08-26_p5_promote_ready.py`), the #1326
   ledger comment `issuecomment-5431097629`, and **ml#1403 (open)**, which fixes two census columns
   that failed into plausible values: `advisory_flag` matched `--advisory` anywhere in the workflow
   text (comments included — every de-advisoried workflow mentions the flag in a comment, and ml
   keeps a real `--advisory` on its `relocation_check.py` invocation), and `gh_api` turned any
   non-2xx (a rate limit) into "file absent", which once reported canopy's `docs/REFERENCE.md` as
   NONE. Until ml#1403 merges, probe invocation lines and files directly; cascor and recurrence
   are the genuine REFERENCE.md 404s (step e), canopy has one.
4. **MEMORY.md is ~19KB against a 24.4KB read limit** with 12 sessions appending; the harness hook
   asks for < 17.1KB. This session trimmed the over-long rows and evicted six duplicate rows (−1.7KB);
   the rest is a P0-style round-2 eviction — an owner decision (the recorded policy is a cap on NEW
   entries only). Do not bulk-rewrite rows other live sessions own.
5. **Owner decisions unchanged** (soak's null-experiment question; worktree convergence LEAVE IT;
   Skills deferred; the MEMORY.md cap). Do not re-propose.

### Key context

- `Memory Budget` reads `skipped` on every `main` commit in the seven `ci.yml` repos
  (`if: github.event_name == 'pull_request' || 'merge_group'`); recurrence's standalone workflow
  publishes nothing on `main`. `observed_contexts()` reads PR-head check-run names,
  conclusion-agnostic. Both are recorded in plan §P5 step d.
- `--ratchet` only LOWERS an existing ceiling (`if chars < ceiling`); seed a fresh repo with the
  helper's `render-config` (measured size) first — plan step b is fixed.
- `measure-growth --ref origin/main` (after a fetch) is the form that cannot go stale; without it
  the helper measures the checkout's HEAD. `render-*` always measure the checkout, by design.
- A raw `grep -c -- --advisory` on a ported `ci.yml` counts COMMENTS that mention the flag (2–3 in
  every repo, removed or not); read the `python3 util/memory_budget_check.py` invocation lines instead.
- **Eight parallel refuting agents (4 lenses × 2 docs) died on the API session limit before
  reporting**, as the peer's four had the night before. With 10+ peer sessions on this machine
  sharing the quota, run the lenses sequentially in ONE session against primary sources — ~40
  read-only probes found 2 MAJOR per document.
- In this bypass-permissions session `;` / `&&` / `$(…)` and plain `git -C <sibling>` all executed;
  a sibling session the same day WAS refused on the word `enable`, so the classifier is word/shape-
  keyed, not mode-keyed (memory updated).
- Merge path that worked today, twice: one signed commit → `gh pr create` → `gh pr merge --squash
  --auto --subject … --body-file …` → `state=OPEN armed=true` → each time `main` moves, `gh api
  repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT` (auto-merge does NOT update the branch by
  itself under the strict policy; #1398 needed it twice) → `util/wait_for_checks.py --pr N`. Merges
  only under Paul's explicit approval (granted session-wide for this arc today).

## Verification commands

```bash
git fetch origin
gh pr view 1398 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid[0:8])"'   # MERGED 19:43Z d95759f8
gh pr view 529 --repo pcalnon/juniper-canopy --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid[0:8])"'   # MERGED 19:34Z 9f6fac97
git show origin/main:notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md | grep -c "all 8 BLOCKING"   # 1
gh issue view 1326 --repo pcalnon/juniper-ml --json title --jq .title
gh api repos/pcalnon/juniper-deploy/contents/.github/workflows/ci.yml --jq .content | base64 -d | grep -n -A3 "python3 util/memory_budget_check.py"   # no --advisory line; one command per repo
python3 util/ad-hoc/2026-08-20_require_context_safely.py --status --context 'Memory Budget'                              # observed YES x7 + ml ALREADY REQUIRED; add --repo juniper-recurrence
python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth /home/pcalnon/Development/python/Juniper/juniper-cascor --days 30 --ref origin/main   # prints "(origin/main)"
python3 -m unittest tests/test_p5_port_memory_budget.py   # 26 OK
python3 util/memory_budget_check.py     # OK 37,019 / 38,000
```

## Git status at handoff

- Worktree `.claude/worktrees/idempotent-dreaming-panda`; branches: `docs/p5-status-8-of-9-and-handoff-validation`
  (ml#1395, MERGED, local deleted), `feat/p5-helper-measure-growth-ref` (ml#1398, MERGED
  `d95759f8`, local deleted), and `docs/p5-preconditions-shipped-and-continuation-handoff`
  (this file + the plan banner/table/step-d record). No other uncommitted work.
- Closed-PR branches kept on origin: `chore/p5-toolkit-seed-and-render` (`cb8a4b73`),
  `docs/p5-status-rates-and-hazards` (`903c208a`).
