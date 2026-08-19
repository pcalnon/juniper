# Direct-Push Prevention — the no-bypass `pull_request` ruleset

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-18
**Status**: **APPLIED** to all 9 repos
**Implements**: recommendation **R5** of
[`…_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md)

---

## 1. The problem R5 addresses

Direct pushes to `main` are the dominant remaining threat to `main`'s health, and **no per-PR control
has jurisdiction over them** — there is no PR to gate.

Measured by two independent audits:

- **5 of juniper-ml's 9** post-adoption `main` breakages came from direct pushes with **no PR at all**.
- **Both** true content-destruction events of the strict era were direct pushes:
  - juniper-ml `76e4513b` — three deletion runs of 16/14/16 lines from the CLI-experimentation plan,
    healed by `40230d2b`, a *restore* commit.
  - juniper-cascor `4d07a88c` — `findings=136, by_verdict={'LOST': 136}`, five whole
    `src/snapshots/*.py` modules, healed 30 minutes later by `d8ae2f97`.

Neither `strict` nor the per-PR sequence-safety screens can see this path. The post-merge `main-verify`
G3 screen does — it caught both — but that is detection-then-repair, not prevention.

## 2. Why a SECOND ruleset, and why this is not "adding a rule"

Direct pushes were **never permitted**. The existing ruleset already carries a `pull_request` rule, and
rule suites show it firing: `pull_request: fail "Changes must be made through a pull request"` — while
the push lands anyway, because the suite result is `bypass`.

**Bypass actors are per-ruleset.** The main ruleset grants `RepositoryRole 5` (owner) an `always`
bypass, which makes every rule in that ruleset advisory for that actor.

That entitlement is genuinely load-bearing — it covers squash-SHA races (where the merge commit has no
reports yet), unresolved review threads, and emergency access — so it is **not** being removed. Instead
a second ruleset carries the same `pull_request` rule with an **empty** `bypass_actors` list. GitHub
evaluates both, so the no-bypass copy binds everyone including the owner, while the original keeps its
bypass for the other seven rules.

## 3. What was applied

| Repo | Ruleset id | Repo | Ruleset id |
| --- | --- | --- | --- |
| juniper-ml | `21018943` | juniper-cascor-client | `21019069` |
| juniper-cascor | `21019063` | juniper-cascor-worker | `21019070` |
| juniper-canopy | `21019065` | juniper-deploy | `21019071` |
| juniper-data | `21019066` | juniper-recurrence | `21019073` |
| juniper-data-client | `21019067` | | |

All identical: name `juniper-no-direct-push`, `target: branch`, `enforcement: active`,
`bypass_actors: []`, conditions `{include: ["~DEFAULT_BRANCH"], exclude: []}`, and exactly one
`pull_request` rule with the **least-restrictive** parameters
(`required_approving_review_count: 0`, all the review toggles `false`, all three merge methods allowed).

The parameters are deliberately permissive: both rulesets' `pull_request` rules are evaluated, so
anything stricter here would silently tighten the *merge* policy as a side effect of a change meant
only to close the *push* path.

Tool: `util/ad-hoc/2026-08-18_no_direct_push_ruleset.py` (`--dry-run` default, `--status`, `--remove`).

## 4. Verified behaviour — and three traps found while verifying

Tested live on juniper-ml by temporarily extending the ruleset to a throwaway ref
(`refs/heads/zz-ruleset-probe`), so `main` was never at risk. The probe branch and the extra condition
were removed afterwards.

1. **A ref UPDATE is rejected, even for the owner** — the intended behaviour:

   ```text
   remote: error: GH013: Repository rule violations found for refs/heads/zz-ruleset-probe.
   remote: - Changes must be made through a pull request.
   ! [remote rejected] HEAD -> zz-ruleset-probe (push declined due to repository rule violations)
   ```

2. **A branch CREATION is NOT rejected** by this rule. Irrelevant for `main`, which already exists —
   but do not assume this rule prevents new branches. Creation is governed by the `creation` rule.

3. **`git push --dry-run` does NOT evaluate rulesets.** It reported the push would succeed
   (`8ecfbf7..654354c HEAD -> main`, exit 0) against an active rule that then rejected the real push.
   **Never use `--dry-run` to verify a ruleset** — it is a false-negative trap of exactly the kind this
   whole arc has been about.

Post-application checks: `BLOCKING=0` on all 9 in the context audit (unchanged), every existing
ruleset intact, and open PRs still `MERGEABLE`.

## 5. Pre-flight that made this safe

A rule that blocks pushes to `main` breaks any automation that pushes to `main`. Checked across all 9
repos: **none does.** The only `git push` call sites in any workflow are the three
`lockfile-update.yml` arms in juniper-data-client, juniper-cascor-client and juniper-cascor-worker,
which run on `dependabot/pip/**` branches and push the regenerated lockfile *there*, not to the default
branch. Every other match is a comment about the never-push-a-bare-tag release convention.

## 6. The cost, stated plainly

**Emergency direct fixes to `main` are now impossible.** A broken `main` must be repaired through a PR
that passes the required checks. `util/safe_merge.py` makes that path cheap and safe, but it is not
instant.

This was an explicit trade: prevention was chosen over the emergency hatch, with the post-merge net
retained.

## 7. Rollback

One call per repo, or all nine at once:

```bash
python util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --status
python util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --remove --execute
```

Removing this ruleset restores exactly the previous behaviour; nothing else was modified. The original
per-repo ruleset was never touched.

## 8. The net that stays

`main-verify.yml`'s post-merge `Symbol & Docs Screen` continues to run on every push to `main` and
still upserts a stable-title dedup tracking issue plus a Slack post on failure. It remains the last
line of defence for anything that reaches `main` through a PR, and it is what caught both historical
direct-push losses.

Its known operational cost is unchanged: the G3.1 catch-up base means one unrepaired finding reds every
subsequent merge until healed (18 consecutive reds in one observed episode). That is a property of the
screen, not of this change.
