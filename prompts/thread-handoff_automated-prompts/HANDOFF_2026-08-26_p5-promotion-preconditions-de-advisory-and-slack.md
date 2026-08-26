# HANDOFF — P5 promotion preconditions 2–4 shipped fleet-wide: `--advisory` gone, slack declared, none promoted

**Date**: 2026-08-26
**Origin session**: `memory budget` (worktree `temporal-squishing-bengio`), started from
[`HANDOFF_2026-08-25_p5-four-ports-and-helper-fold.md`](HANDOFF_2026-08-25_p5-four-ports-and-helper-fold.md)
**Peer session (same day, concurrent)**: `p5 ports, session split [3c9662]` — owns the plan §P5 banner /
docstring / four-lens validation lane (ml#1395 MERGED `d038258f`, ml#1398 `measure-growth --ref` restore) and
was waiting for the per-repo merge figures below to update the plan banner.

**Validation status: SELF-REVIEWED ONLY.** Every figure below was read back from `gh` after the fact, but no
independent refutation pass ran. The arc's record: parallel refuting agents (8, then 4) died on the API
session limit twice on 2026-08-26 — run the four lenses **sequentially in one session** against primary
sources before acting on the tables.

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** arc in `juniper-ml`, P5 fleet rollout, **promotion phase**. State at
handoff: all 8 governable repos carry the memory-budget ratchet (P5 ports, merged 2026-08-25/26), and
**plan §P5 step d preconditions 2–4 are shipped in all 8** — `--advisory` removed, the three negative
controls re-run against the non-advisory invocation, real slack declared with `Allow-Ceiling-Raise:
AGENTS.md`. **NONE is promoted to a required context.** That ruleset write is the owner's explicit call;
this session had merge approval for its PRs, not promotion approval.

Authorities: plan §P5 in `notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` (step d = the
four preconditions; step e = G3 + the cut, which needs `docs/REFERENCE.md` created first in cascor and
recurrence); tracker **ml#1326** (the comment thread is the live ledger); the peer's corrections in ml#1395.

### Completed this session

| Repo | PR | Ceiling (chars) | Slack | mergedAt (UTC) | squash |
|---|---|---:|---:|---|---|
| juniper-deploy | #196 | 34,569 → 36,569 | +2,000 (floor) | 18:08:48 | `1fe58592` |
| juniper-recurrence | #132 | 11,578 → 13,698 | +2,120 (max) | 18:09:00 | `a80a7dc9` |
| juniper-cascor-worker | #163 | 35,126 → 37,126 | +2,000 (floor) | 18:18:47 | `cf5ae76d` |
| juniper-cascor-client | #140 | 34,695 → 37,277 | +2,582 (max) | 18:18:59 | `87464c35` |
| juniper-data | #294 | 43,493 → 45,493 | +2,000 (floor) | 19:18:02 | `e0b738e6` |
| juniper-cascor | #591 | 71,098 → 80,707 | **+9,609** (its max) | 19:18:13 | `c6cd2f09` |
| juniper-data-client | #174 | 28,369 → 30,442 | +2,073 (max) | 19:19:14 | `a3226826` |
| juniper-canopy | #529 | 95,133 → 97,133 | +2,000 (floor) | **IN FLIGHT** — `safe_merge` re-sync cycle 2, head `c66e1c32`, BLOCKED = checks pending | — |

Slack rule (plan step d.4): `max(largest single AGENTS.md-growing commit over 30 days, 2,000)`, re-measured
in a **fresh worktree at origin/main** (the helper's `measure-growth` reads the checkout's HEAD; `--ref`
only exists once ml#1398 lands). The 2,000 floor is the fleet-wide fan-out class — one 2026-08-21 docs
sweep added 1,982 chars to six repos' `AGENTS.md` at once.

Each PR: one YubiKey-signed commit (`verified=true login=pcalnon`), two files (`ci.yml` or recurrence's
`memory-budget.yml`, and `conf/memory_budget.json` with a rewritten `_note`). The `Memory Budget` check
reported **SUCCESS on all 8 PR heads via the non-advisory job** with the log line
`[RAISE-WAIVED] AGENTS.md: <old> / <new> chars headroom=<slack>` — since control 0 proved an undeclared
raise exits 1, SUCCESS there is the trailer path and nothing else.

Controls run per repo by `util/ad-hoc/2026-08-26_p5_promote_ready.py` (provenance; state files in
`~/.local/state/juniper-p5-promote/<repo>.json` + `<repo>.scratch/{COMMIT_MSG.txt,PR_BODY.md}`): raise
undeclared → exit 1 (rule 4); declared → exit 0 RAISE-WAIVED; +slack+500 chars → exit 1; same + loan → exit 0
WAIVED with the budget file byte-identical; restore → exit 0; `--ratchet` on a COPY tightens exactly back to
the old ceiling. Plus workflow re-parse (standalone, non-advisory, trailer-aware), the 40-test ported
suite, and the target's own pre-commit.

Also this session: `util/ad-hoc/2026-08-26_p5_fleet_state.py` (API census, `--dump DIR`) — the
"confirm what the merge run landed" step of the predecessor, all 8 ports verified MERGED with headroom 0.

### Remaining work

1. **Land canopy#529.** `gh pr view 529 --repo pcalnon/juniper-canopy --json state,mergedAt,mergeCommit`. If
   still OPEN: `python3 util/safe_merge.py --repo juniper-canopy --pr 529 --merge-method squash --execute
   --no-auto-fallback` once more (canopy's `main` moved twice during the run; a second invocation merged
   data/cascor cleanly). Look for the `MERGED #529` line, never the exit code. If it thrashes a third time,
   the memory's fallback is native `gh pr merge --squash --auto --subject/--body-file` (body from the
   scratch dir, subject line stripped).
2. **Post-merge verification, all 8**: `Post-Merge Main Verification` green on each repo's `main`
   (`gh run list --repo pcalnon/<repo> --branch main --limit 3`), and re-run the census — expect
   `advisory=False`, banner `BLOCKING`, `required=False`, `headroom == slack` everywhere. The merge run
   was owner-authorized; nothing post-merge re-checks the raise (the job is `skipped` on `main` by
   design), so the census is the proof.
3. **Ledger + peer.** Post ONE comment on ml#1326 with the table above (mergedAt/squash for #529 filled
   in), and message peer `p5 ports, session split [3c9662]` (address
   `uds:/run/user/1000/cc-socks/1210948.sock`) the same figures — it holds the plan banner update. If the
   peer is gone (`ListAgents`), update plan §P5's status banner yourself: "preconditions 1–4 met in all 8;
   promotion (ruleset) = owner decision" with the table; §4a says status may not be left stale.
4. **Archive PR for this handoff + the two scripts** (branch
   `docs/handoff-2026-08-26-p5-promotion-preconditions`, from `origin/main` `d9052022`): merge when green
   — the owner's approval for this session's PRs covers it. Eight PR bodies cite the script path as
   provenance, so it must land.
5. **Promotion — owner's explicit go required, per repo.** Dry-run first, then write:
   `python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-<x> --context 'Memory Budget'`
   (`--status` shows "would add"; observed YES everywhere from the PR heads), then `--apply`. Never
   `--allow-unobserved`, never `add_required_context.py`. `--repo` is required for recurrence (not in the
   default roster). With slack declared, the first fan-out fits every ceiling; cascor's 9,609 is deliberately
   large and comes back down at the cut.
6. **Worktree cleanup, after MERGED + liveness probe** (`util/ad-hoc/2026-08-20_worktree_liveness_probe.py`),
   reading the owner's arc approval as the post-merge tail on this session's OWN worktrees, as the 08-26
   precedent did: the eight `<repo>--feat--memory-budget-blocking--20260826-12xx--<sha>` dirs under
   `/home/pcalnon/Development/python/Juniper/worktrees/`, then `git -C <primary> branch -d
   feat/memory-budget-blocking` + `worktree prune` in each sibling primary, then fast-forward each primary
   if it is on `main` and clean (`status -sb` first). `worktree remove` deletes ignored files. The ml
   primary pull is an owner action from an isolated session.
7. **Step e stays owner-sequenced**: `docs/REFERENCE.md` must exist in cascor and recurrence before any cut;
   the cut lands on `main` with the primary pulled BEFORE any worktree carries the trimmed file (plan hazard).
8. Owner decisions carried forward unchanged: soak rung 1 (policy stratum 24/24), parent `Juniper/AGENTS.md`,
   worktree settings asymmetry (LEAVE IT), MEMORY.md 120-byte cap on new entries.

### Key context

- **Do not touch `util/ad-hoc/2026-08-25_p5_port_memory_budget.py` or `tests/test_p5_port_memory_budget.py`**
  until the peer's ml#1398 lands (it restores `measure-growth --ref`).
- **Trailers**: git parses trailers from the LAST paragraph only. A blank line between
  `Allow-Ceiling-Raise:` and `Co-Authored-By:` left `%(trailers:key=…)` empty (the checker's MULTILINE regex
  would still have matched) — all trailers now sit in one final paragraph, and `ship` verifies both readings.
- **`safe_merge` on a fleet run**: three of eight went BEHIND between "green" and "merge" as sibling `main`s
  moved; it re-syncs once and REFUSES after 540 s with "required checks did not finish" — that is the tool
  working. A second invocation on the now-green head merges. Squash message for a re-synced PR concatenates
  the `Merge branch 'main'` line (`COMMIT_MESSAGES` setting) — cosmetic here, nothing post-merge reads it.
- **This `gh` has no `gh pr checks --json`** and no `--json baseRefOid`; use `gh pr view --json
  statusCheckRollup` / compare `headRefOid` to `commits/main`. `mergeStateStatus` reads UNKNOWN/BLOCKED
  transiently while GitHub recomputes — data-client showed BLOCKED with zero review threads and was CLEAN
  a minute later.
- **Interpreters for the ported suite**: canopy/cascor/data need their own envs (`-q` already in canopy's
  and cascor's `addopts`, so never add another `-q` — `-qq` drops the summary line); cascor-worker's
  `tests/conftest.py` imports the package and needs `juniper_config_tools` → JuniperCascor1.
- The shell gate refuses `for` loops and `$(…)` from a worktree-isolated session; plain commands, `;`/`&&`
  chains and `git -C <sibling>` work. That is why both scripts exist.
- The ml `conf/memory_budget.json` `_README` still says "standalone advisory 'Memory Budget' job" — stale
  since P4 (ml is BLOCKING + required). One-word fix; not done here to keep out of the peer's docs lane.

### Verification commands

```bash
git fetch origin && git rev-parse --short=8 origin/main          # d9052022 at handoff
python3 util/ad-hoc/2026-08-26_p5_fleet_state.py                 # all 8: advisory False, BLOCKING, required False, headroom == slack
gh pr view 529 --repo pcalnon/juniper-canopy --json state,mergedAt,mergeCommit,mergeStateStatus
gh pr view 591 --repo pcalnon/juniper-cascor --json state,mergedAt,mergeCommit --jq '.mergeCommit.oid[0:8]'   # c6cd2f09
gh api repos/pcalnon/juniper-cascor/contents/conf/memory_budget.json --jq .content | base64 -d | grep ceiling_chars   # 80707
python3 util/ad-hoc/2026-08-20_require_context_safely.py --status --context 'Memory Budget' --repo juniper-cascor    # "would add", observed YES
python3 util/ad-hoc/2026-08-26_p5_promote_ready.py status juniper-canopy                                             # state file incl. pr/head
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep memory-budget-blocking                                  # 8 dirs until cleanup
```

## Git status at handoff

- juniper-ml session worktree `.claude/worktrees/temporal-squishing-bengio`, archive branch
  `docs/handoff-2026-08-26-p5-promotion-preconditions` from `origin/main` `d9052022`, carrying this file plus
  `util/ad-hoc/2026-08-26_p5_fleet_state.py` and `util/ad-hoc/2026-08-26_p5_promote_ready.py`.
- Eight sibling worktrees (branch `feat/memory-budget-blocking` in each primary), all pushed, PRs as tabled:
  `juniper-deploy--…--20260826-1236--7e046491`, `juniper-canopy--…--20260826-1238--50fbde0d`,
  `juniper-cascor--…--20260826-1238--67d7ea35`, `juniper-cascor-client--…--20260826-1238--b1c1acd7`,
  `juniper-recurrence--…--20260826-1239--369d8f59`, `juniper-data-client--…--20260826-1239--918f1dee`,
  `juniper-data--…--20260826-1239--68f7b5e4`, `juniper-cascor-worker--…--20260826-1239--177c2a15`
  (`…` = `feat--memory-budget-blocking`). Their working trees are clean; each carries exactly one commit.
- Nothing stashed; nothing uncommitted outside the archive branch.
