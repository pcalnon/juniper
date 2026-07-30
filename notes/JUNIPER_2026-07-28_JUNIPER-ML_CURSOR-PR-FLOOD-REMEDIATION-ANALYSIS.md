# Cursor-Fleet PR-Flood Remediation — Analysis of Record

**Project**: Juniper — juniper-ml (meta-package)
**Author**: Claude (flood-remediation program orchestrator), for Paul Calnon
**Date**: 2026-07-28
**Status**: Complete — heal PRs #852/#853 MERGED (2026-07-29 03:14/03:15Z); censusclean verified ON MAIN at `23024f5`; three validated guardrail proposals awaiting owner decisions
**Program prompt**: `prompts/generated/JUNIPER_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION_PLAN_2026-07-28_0315.md` (merged via ml#844)
**Grounding**: main `3915d1e6` (= Phase-0 anchor `ac2ec9d7` + ml#844); discovery bundle all-probes-ok; ruleset 13805432 live-probed

---

This document is the single record of the 2026-07-25→28 Cursor-fleet PR-flood remediation program: (1) the incident narrative and consolidated root cause, (2) the definitive damage census with heal PRs, (3) three independently-validated guardrail proposals with their validation records and a comparison matrix, (4) the owner decision list, and (5) the process-validation record. The program performed no merges, no repo-settings changes, and no Cursor-dashboard changes — its only writes are the
owner-merge heal PRs and this document's PR.

---

## §1 Incident narrative & root cause

*Evidence tags: `[ruleset]` = live `gh api repos/pcalnon/juniper-ml/rulesets/13805432`; `[universe]` = the pinned census JSON `scratchpad/flood_census_universe.json` (computed at main `3915d1e6`); `[git]` = local history probe at `3915d1e6`; `[gh]` = read-only `gh pr view`; `[apps]` = `gh api /apps/cursor`;*
*`[memory]` = owner incident log `project_juniper_ml_concurrent_session_activity.md` §"2026-07-26: Cursor Automation fleet"; `[Phase-0]` = the 2026-07-28 two-agent forensic pass (numbers not cheaply re-derivable at HEAD).*

### (a) Incident narrative and quantified scope

Over roughly 25 hours the Cursor agent fleet opened **134 PRs** against `pcalnon/juniper-ml` (span **#710–#843**), plus the window-edge **#709** and the remediation-plan PR **#844** `[Phase-0]`.
By class the 134 created split **63** `cursor/missing-test-coverage-*`, **57** `cursor/engineering-documentation-updates-*`, **6** `cursor/critical-bug-investigation-*` (126 cursor) and **8** non-cursor incl. heals #838/#842/#843 `[Phase-0]`. Outcome: **133 merged, 1 closed (#743), 0 open** `[Phase-0]`.
The census universe — 135 first-parent `Merge pull request #` merges by merge-date, span **#709–#844** — reconciles this exactly: **125 cursor merged** (63 test-coverage / **56** docs / 6 bug-investigation) plus 10 non-cursor; docs drops 57→56 because the single closed PR #743 is a docs branch `[universe]`.

Creation ran **2026-07-25 19:41Z → 07-26 20:14Z** containing a ~10-hour lull, with merge activity continuing through 07-28; the creation rate peaked at **48 PRs per fixed 6-hour UTC bucket**, with same-second dispatch pairs observed `[Phase-0]`. This is a recurring pattern, not a one-off: prior monthly cursor-PR volumes were **2026-03: 47, 05: 10, 06: 28, 07: 130** `[Phase-0]`. The owner's "600+" recollection is the **repo-lifetime closed-PR counter (835)**, not this window `[Phase-0]`.

Merge mechanics were **100% true merges (no squashes)**; **136** `Merge branch 'main' into <branch>` union-carrier commits rode in on second parents — re-verified exactly at HEAD (committer-date window 07-25…07-29) `[git]`. There is no `merge=union` gitattributes driver; the damage is ordinary 3-way (ort) hunk fusion/loss on append-heavy files during stale-branch refreshes `[Phase-0]`.

### (b) Root-cause chain (each link with its evidence)

1. **Cursor GitHub App is the source.** The app is integration **id 1210556** — confirmed directly: `gh api /apps/cursor` → `{"id":1210556,"name":"Cursor","slug":"cursor"}` `[apps]`.
   Fleet PRs are authored by the bot `app/cursor` and carry **per-class automation UUIDs** in their bodies: #729 (test-coverage) → `4e249ce1-d08d-4b6a-b9a7-6897dc9852d0`; #746 (docs) → `294b2ed6-5c33-4413-aea6-450ca4fdb9b7`, each with a distinct `cursor.com/agents/bc-…` link `[gh]`. All configuration lives on the Cursor dashboard; there is **no in-repo config** `[Phase-0]`.
2. **Same-file fan-out clusters.** Many independent branches append to the same few files. Top clusters, counted across the 135 window merges `[universe]` (Phase-0 value in parens):
   `AGENTS.md` **54** (53), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` **53** (53), release-train operator runbook **34** (33), `docs/REFERENCE.md` **15** (15); tests `test_release_train_detect.py` **12** (12), `_workflow_guard` **10** (10), `_ceremony` **11** (10), `_propose` **9** (9), `test_worktree_cleanup.py` **10** (10).
   The small `+1`s (AGENTS/runbook/ceremony) are window-edge drift — my HEAD `3915d1e6` sits 2 merges past Phase-0's `ac2ec9d`; universe buckets read tests 77 / util 17 / doc-union 62 / ci.yml 9 vs Phase-0 76/16/61/9 `[universe]`.
3. **Ruleset `juniper-ml-rules` (id 13805432) gaps** `[ruleset]`: `required_status_checks.strict_required_status_checks_policy: **false**` (branches need NOT be up to date before merge); the `rules` array carries deletion, non_fast_forward, code_scanning, code_quality, required_status_checks, required_signatures, update, creation — but **no `pull_request` (required-review) rule** and **no merge-queue rule**. CODEOWNERS is therefore advisory only.
4. **Always-bypass actors.** Five actors hold `bypass_mode: always`: `DeployKey`, `RepositoryRole` (id 5), and Integrations **1210556 (Cursor)**, **1236702**, **1276151** `[ruleset]`. The Cursor app itself can bypass; 1236702 resolves to **claude** via `gh api /apps/claude`; only 1276151 stays unidentified (see (e)).
5. **Owner manual true-merges + web "Update branch".** With strict=false, each of the 125 cursor PRs was manually true-merged; stale branches were refreshed via GitHub-web **Update branch**, whose commits show **committer `GitHub`** (the web-flow identity) and author the owner's GitHub account.
   Spot-checked on three `Merge branch 'main' into cursor/…` carriers (`b1adc5b`, `be844d8`, `37b418a`): `committer=GitHub`, `author=Overtoad` `[git]`. (Phase-0 recorded the author as `pcalnon`; same owner account, display-name nuance — the load-bearing evidence is committer=`GitHub` = the web mechanism.)
6. **Ort 3-way fusion/loss → green-on-green damage.** Those refresh merges fused/deleted sibling content that was individually green on each branch, so damaged states merged **green** — the mechanism the flat CI + advisory review could not see `[memory]`.

### (c) Failure-class taxonomy (from the incident log) `[memory]`

- **Empty-stub + NameError** — bad conflict resolution left an always-pass stub and an undefined name. *Exemplar #751* (fleet even opened restore PR #800).
- **Helper-deletion-with-live-callers** — a merge deleted a helper its own tests still call. *Exemplar #729.*
- **Fused-method-bodies** — a merge kept one method's signature but another's body (F821 on donor locals / mypy attr-defined). *Exemplars #738 (into main), #782 (on-branch).*
- **Byte-identical-duplicates** — merge retained duplicate members; mypy no-redef catches it, flake8 does not. *Exemplar #729.*
- **Silent test-block deletion** — a merge dropped a sibling test block/method with all lint green. *Exemplars #738 (deleted #759's Phase-3 block); the 23:01Z batch dropped `test_skip_remote_delete_flag_skips_gh_and_push` and weakened two guard bodies.*
- **Docs wholesale-section deletion** — a docs merge took the branch side across AGENTS.md/REFERENCE.md/cheatsheet, deleting sibling sections merged hours earlier; only symptom CI sees is a dangling anchor. *Exemplars #801, #803.*
- **Stale merge-ref pre-commit contamination** — main briefly non-black-clean makes every PR's `pre-commit --all-files` merge-ref run fail regardless of its own content. *Exemplar #759.*
- **Stale-base PR file lists** — GitHub computes a PR's file list vs a stale base; #729 showed 12 files (incl. an unparseable test) but the true post-`merge origin/main` delta was 2 pure-intended files. *Exemplar #729.*

### (d) What already healed

- **#838** *"fix(tests): unbreak main CI — black format + repair #738-merge damage (restore dropped Phase-3 tests)"* — MERGED 07-27 22:54Z `[gh]`.
- **#842** *"fix(tests): restore 5 tests + assertion bodies lost in the 23:01Z merge batch"* — MERGED 07-27 23:11Z `[gh]`.
- **#843** *"fix(tests,docs): restore symbols lost in the #813–#820 merge wave"* — MERGED 07-27 23:56Z `[gh]`.
- **Proven repair recipes** `[memory]`: **graft-method** restore — take main's file wholesale and re-graft each branch's additions verbatim from `<merge-sha>^1` (the canonical last-good main-side blob), AST-verifying byte-identical dupes before deleting;
  and the **`git log -m -S<symbol>`** unmasking technique — a plain `-S` finds nothing when a deletion happened inside a merge resolution, so `-m` is required to attribute the loss to its guilty merge. The primary checkout, found parked on #782's branch (338 behind), was restored to main `[Phase-0]`.

### (e) Owner-side open probes to REQUEST (not performed here)

- **Identify always-bypass integration 1276151.** (1236702 resolved to the **claude** app via its slug — `gh api /apps/claude`; numeric-id endpoints 404.) 1276151 does not resolve via the public API `[git]`, so the owner must read it from **Settings → Integrations / Installed GitHub Apps** (or their app slugs). Decide per-integration whether always-bypass is intended.
- **Retrieve the three Cursor dashboard automation configs** behind the per-class UUIDs (test-coverage `4e249ce1-…` from #729; docs `294b2ed6-…` from #746; plus the bug-investigation class): **schedule/cadence, concurrency cap, per-class prompts, and file-scope settings** — the control surface is entirely the Cursor dashboard, invisible to the repo.

### §1 addendum — post-consolidation corrections (validation round)

- **The "monthly storm" framing is corrected to bimodal.** Re-derived cursor-branch merge counts by merge-date (`git log --merges --since=<M-01> --until=<next-M-01> --format='%s' origin/main | grep -c 'from pcalnon/cursor/'`): 2026-01: 0, 02: 0, 03: 43, 04: 0, 05: 10, 06: **0**, 07: **129**. Phase-0's per-month figures (47/10/28/130) reproduce for May and approximately for July; March differs slightly (43 vs 47); June does **not** reproduce by merge-date (0 merged of 4 total June merges). The
  likely reconciliation is created-vs-merged bucketing (June-created cursor PRs merging in July), so the honest statement is: cursor activity recurs, but the *storm* pattern by merge-date is bimodal (2026-03 and 2026-07), not monthly.
- **Update-branch author identity nuance**: spot-checked carrier merges show `committer=GitHub` with the owner's account (`Overtoad` display) as author — Phase-0 recorded `pcalnon`; same owner account, and the load-bearing evidence for the web Update-branch mechanism is the `GitHub` committer identity.
- **Docs class count nuance**: 57 docs-class PRs were *created*; 56 merged (the single closed PR #743 was a docs branch).

---

## §2 Damage census (Task 1)

### §2.1 Pinned universe

Computed once at `3915d1e6` and shared by every census agent (`util/ad-hoc/2026-07-28_flood_census_universe.py`, committed with this PR): window merges = `git log --first-parent --merges --since=2026-07-25 --until=2026-07-29 origin/main` filtered to `Merge pull request #`; per-merge touched files = the PR-files metric `git diff --name-only $(git merge-base <M>^1 <M>^2) <M>^2`. Result: **135 merges / 77 test-touching / 17 util-touching / 62 doc-union-touching / 9 ci.yml-touching**. Reconciliation
vs Phase-0's 134/76/16/61/9: the +1 on tests/util/docs is **#709** (window-edge — merged 2026-07-25 19:02Z, caught by the literal local-time `--since`; Phase-0's span statement began at #710), and the +1 total is **#844** (the program-plan PR itself, prompts-only). Both within the plan's ±1 tolerance; both retained. Main advanced during program execution (post-pin: v0.7.0 #845, release merges #848–#850, and the heal PRs #852/#853); post-pin merges are outside the pinned universe by construction.

### §2.2 Python census (C1, corrected by C3/C4) — final: 20 test classes + 13 method/helper grafts (~71 methods) LOST-IN-MERGE; util source clean

Method: AST symbol inventory (classes, qualified methods, module functions/constants/imports; bash function inventory) at every touching merge's `<M>^1` main-side blob vs current main, deduped by blob (145 distinct blobs, 2078 symbol comparisons across 40 files); every candidate adjudicated via `git log -m -S<symbol>` (the `-m` flag unmasks merge-resolution deletions) into LOST-IN-MERGE vs INTENTIONAL; known-good waypoints `bd25e31` (post-#842) and `df32640` (#843) cross-checked. Coverage: 77
tests-touching ∪ 17 util-touching merges; zero in-universe files skipped (verified); zero unparseable blobs.

Findings (verdict LOST-IN-MERGE unless noted; last-good blob = `<guilty>^1:<path>`):

| file                                       | class (methods)                                                  | guilty merge     | evidence                                                                       |
|--------------------------------------------|------------------------------------------------------------------|------------------|--------------------------------------------------------------------------------|
| tests/test_juniper_chop_all.py             | TestValidatePid (10)                                             | #778 `a0b3a192d` | `validate_pid` still in script; 0 test mentions at HEAD                        |
| tests/test_juniper_chop_all.py             | TestGracefulStop (4)                                             | #791 `1a55e1310` | SIGTERM/SIGKILL suite gone                                                     |
| tests/test_juniper_chop_all.py             | TestOrphanedWorkerCleanup (7)                                    | #798 `e92a7eed3` | KILL_WORKERS behavioral gone; AGENTS.md still documents the class              |
| tests/test_juniper_plant_all.py            | TestCheckPortAvailable (3)                                       | #788 `38daab3d3` | HEAD covers worker-port only                                                   |
| tests/test_juniper_plant_all.py            | TestCleanupOnFailure (4)                                         | #788 `38daab3d3` | SIGTERM/pidfile suite gone                                                     |
| tests/test_juniper_plant_all.py            | TestWaitForHealth (2)                                            | #788 `38daab3d3` | healthy/timeout behavioral gone                                                |
| tests/test_juniper_plant_all.py            | TestValidateCondaEnv (5)                                         | #795 `ffb363ec3` | all-envs/missing-dir/non-exec arms gone (restored during incident #5, re-lost) |
| tests/test_juniper_plant_all.py            | TestWaitForHealthIntervalGuard (2)                               | #795 `ffb363ec3` | interval-clamp guard gone (same re-loss)                                       |
| tests/test_juniper_plant_all.py            | TestSafeCondaActivate (2)                                        | #804 `4eb38611b` | #785/#795 nounset restore-test gone; AGENTS.md still documents it              |
| tests/test_isolated_stack_script.py        | TestActivateCondaNounset (3)                                     | #786 `e239e69dc` | #785 nounset restore-test gone                                                 |
| tests/test_isolated_stack_script.py        | TestLiveDown (1), TestPortPid (2), TestStopPort (3)              | #793 `406dfe891` | live teardown coverage gone (`do_down`: 0 mentions)                            |
| tests/test_isolated_stack_script.py        | TestDryRunStatus (1), TestProbeHealth (4), TestWaitForHealth (3) | #807 `6caefd5c7` | status/health behavioral gone (#843 restored only TestDataUpLive)              |
| tests/test_editable_install_drift_check.py | DriftCheckTest run_fix tests (3) + `_resolvable_plan`            | #795 `ffb363ec3` | `run_fix` exists in util; 0 `test_run_fix_*` at HEAD; #795-clobber pattern     |
| tests/test_release_train_detect.py         | UploadTimeTest (2)                                               | #761 `905e339f8` | `_upload_time` exists in detect.py; sole HEAD ref is fixture data              |
| tests/test_worktree_cleanup.py             | TestPhase1DirtyTree (1)                                          | #731 `6c090a5e9` | #747 dirty-exit-1 gate arm gone                                                |
| tests/test_worktree_cleanup.py             | TestPhase7Behavioral (3) — ADJUDICATE                            | #742 `c4f089636` | live checkout-refusal/dirty-skip arms vs HEAD's dry-run-only coverage          |
| tests/test_worktree_cleanup.py             | TestPhasePullFfOnlyWarnSkip (2) — ADJUDICATE                     | #759 `52931961e` | ff-only tokens present, no dedicated warn-skip method                          |

**Adjudication corrections:** C3 (§2.4) proved C1's same-merge rename-target rule can mis-file real losses as INTENTIONAL; C4's focused re-adjudication flipped 7 more residuals to LOST (ceremony execute-seam ×3 + fixture, detect hygiene-healthy, sweep-safety ×3) and confirmed 2 covered/superseded — final Python-census totals: **20 test classes + 13 method/helper grafts into existing classes (~71 methods total across 8 test files)** (the table above plus the C3/C4 rows detailed in §2.4).

Clean categories: **util/ source CLEAN** (sole candidate = #709's intentional signed-archive refactor of `util/release_train/ceremony.py`); **WEAKENED 0 real** (2 false positives dismissed: a reorg and a black-reflow); **DUPLICATED 0**; **POST-HEAL-REGRESSION 0** (every candidate file byte-identical HEAD==`df32640`).

**ci.yml (9 touching merges) — NOT-CLEAN in one respect**: job structure clean (9 jobs, no duplicate keys — the 2026-06-06 startup_failure class absent; `required-checks.needs` intact), but **4 test-file invocations were merge-dropped from the enumerated battery**, so those files exist at HEAD and never run in CI: `test_cleanup_open_remove_stale_worktrees.py` (#817 `caf9e7afc`), `test_cleanup_session_worktrees.py` (#822 `1659df34f`), `test_global_text_search.py` (#833 `41f5c620a`),
  `test_worktree_wipeout_close.py` (#831 `47f5172ce`). All four verified passing locally at HEAD before healing.

### §2.3 Docs census (C2) — all 6 doc-union files NOT CLEAN

Method: per file, pre-flood baseline = oldest touching merge's `^1` blob; each merge's intended additions = `git log --no-merges <M>^2 --not <M>^1` patches (branch tips are always locally reachable as `<M>^2`); expected content = baseline + all intended additions modulo later legitimate edits; every missing unit adjudicated on main's first-parent timeline (dropped at a 2-parent commit = LOST-IN-MERGE). Reverse screen: **zero pre-flood baseline headings eroded anywhere** — every loss is
flood-added content dropped by a later union merge.

| file                                     | verdict    | salient findings                                                                                                                                                                                                                                    |
|------------------------------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AGENTS.md                                | 2 clusters | F-A1 ceremony signed-archive re-entry bullet (#732 → dropped @#752); **F-A2 major**: `check_conda_env_torch` shipped in code but all doc touchpoints lost incl. its run-list line (heal-adjudicated to 3 touchpoints; see §2.5) (#816 → @#817/#830) |
| docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md  | **severe** | ~19 lost clusters — release-train operator quick-ref near-wiped (tip-at-base safety, HALT states, archive-guard triage, R7 `ref=` rule, drift-check rows, …); e.g. #766 landed net +3/−45                                                           |
| docs/REFERENCE.md                        | major      | F-R1 live `cascor_up`/`canopy_up` compose subsection (#827 → @#829, net +31/−49); F-R2 4 TOC rows; F-R3 two duplicated section headings (additive damage)                                                                                           |
| docs/DOCUMENTATION_OVERVIEW.md           | minor      | 2 quick-task nav rows (#810 → @#812; #812 → @#827)                                                                                                                                                                                                  |
| notes/…RELEASE-TRAIN-OPERATOR-RUNBOOK.md | **severe** | ≥6 whole subsections (SHIP-filter/SemVer, Gate-1 sibling co-change, §4.1 monitor terminals, refusal stubs, seam gates, RESUME_MONITOR mechanics) + 4 duplicated headings                                                                            |
| notes/…WORKTREE-CLEANUP-PROCEDURE-V2.md  | major      | F-W1 whole Phase-4 remote-branch-deletion subsection incl. fail-closed #739 docs (#740/#760 → @#783); F-W2 #733 sweep-apply increments                                                                                                              |

**RESUME_MONITOR fresh adjudication** (per the program mandate): pre-flood 0 mentions; reconstruction says current main should hold **5**; it holds **3**; the 2 missing are the `plan_ceremony`/execute state-machine lines (authored #758, re-added #805, dropped at #809's merge `6cda19ecbb`). The mid-flood "4→2" count is formally superseded.

### §2.4 Completeness critic (C3) and focused re-adjudication (C4)

**C3 — coverage completeness.** Of 58 distinct files touched by the 135 window merges, 47 were covered by C1/C2; the 11 uncovered files (19 touches) were triaged and screened — **all CLEAN**: CHANGELOG.md (3 touching merges reconstructed; all 4 `[Unreleased]` entries survive), the version-dunder-lockstep and isolated-stack-checklist notes (multi-touch; every editing commit reconciles as a HEAD ancestor), the #840/#841 dependabot workflow bumps (land verbatim), the #839 `conf/` CI env snapshots,
  and the #844 prompts add. Notably `pyproject.toml`, `README.md`, `MANIFEST.in`, `.pre-commit-config.yaml`, and all package lockfiles were touched by **zero** window merges — no declared-surface or version change shipped through the flood. Five deterministic spot-checks (lowest-SHA single-file merges): two corroborated C1 findings, two clean, and one exposed a genuine census defect — C1's same-merge rename-target rule had mis-filed 2 lost ceremony execute-seam tests as INTENTIONAL because the
  surviving "replacement" tests a shallower (plan-level) depth.

**C3 method critique (residual-risk register).** (1) The rename-target adjudication rule can false-INTENTIONAL a real loss — realized, corrected by C4 below. (2) C1's top-level `tests/*.py` glob excludes fixture/subdir files — latent only (zero such files touched in-window). (3) Raw line-diff clobber counts overstate loss vs the HEAD-anchored per-symbol screen (e.g. #738's 139 transiently-clobbered lines all healed) — the screen is the correct authority. (4) C2's heading-granularity reverse
  screen could miss intra-section cell drift under a retained heading — benign here. (5) The universe's file set is PR-intent; evil-merge-only edits could hide — checked (40/135 merges carry combined diffs): all touched files were already in coverage; no gap.

**C4 — re-adjudication of the 11 residual rule-based INTENTIONALs.** Verdicts: **7 LOST** — 3 ceremony execute-seam arms (`test_execute_archive_already_on_main_skips_pr_and_cuts_release`, `test_execute_open_archive_pr_reuse_skips_open_and_enables_automerge_on_branch` — whose HEAD "covered elsewhere" comment referenced the dropped test itself — and `test_execute_halt_publish_halts_without_filing_issue` + its `FAILED_PUBLISH_RUN` fixture, guilty #737/#741), the detect hygiene-healthy guard
  (`test_hygiene_healthy_when_release_and_archive_exist`, #761), and 3 sweep-safety arms (`test_dry_run_and_include_ignored_can_combine`, `test_include_ignored_still_hard_skips_tracked_modification`, `test_unknown_flag_exits_2` — a documented contract pin; all #735); **2 properly cleared** — the detect SourceError arm is covered-equivalent at HEAD (`test_local_git_hygiene_tag_only_unavailable_not_false_positive`), and the #715 survey-ignored-dirty drop is a deliberate contract reversal (HEAD
  asserts the opposite arm); **#709's signed-archive refactor confirmed intentional** (local-git capture/restore machinery replaced by the GitHub-API signed-commit seam in the same merge). Mechanism note: all 7 new LOSTs were dropped by clobbering stale-base merges, not removal commits. C3's method flipped C1's INTENTIONAL verdict on 7 of the 9 deep-dived residuals — the census's one systematic weakness, caught by its own critic layer.

### §2.5 Heals

**PR #852 — `fix(tests,ci): restore 20 test classes + 13 method grafts + 4 CI invocations lost in flood merges (census C1/C4)` (branch `fix/flood-census-c1-tests-restore`).** One commit, **+2045 / −0** — purely additive; no HEAD content rewritten or deleted. Restores every C1+C3+C4 finding verbatim from each guilty merge's `^1` blob (AST byte-identical before repo-pinned formatting; module-level support — imports, constants, helpers — grafted with the classes; no duplicate members): the
  chop/plant/isolated-stack class suites, the
  editable-install `run_fix` tests, detect's `UploadTimeTest` + hygiene-healthy guard, the worktree-cleanup Phase-1/ff-only arms, the 5 ceremony execute-seam tests (the 3 C4-flipped arms + the 2 C3-flagged resume-monitor siblings) + `FAILED_PUBLISH_RUN`, and the 3 sweep-safety arms; plus the 4 merge-dropped ci.yml battery invocations re-added in sibling position. Two adjudications resolved: the Phase-7 live dirty-skip/checkout-refusal arms restored while its third arm was SKIPPED-EQUIVALENT
  (HEAD's dry-run test covers the same restore path — evidence in the PR
  body); both ff-only arms restored. Validation: per-file suites green (chop 38 / plant 55 / isolated 55 / editable 20 / detect 85 / worktree 39 / ceremony 87 / sweep 17), **full battery 57/57 files OK including the 4 re-added**, `pre-commit run --all-files` all hooks passed.

**PR #853 — `fix(docs): restore flood-lost documentation across 6 files` (branch `fix/flood-census-c2-docs-restore`).** Restores every C2 finding: AGENTS.md F-A1/F-A2 (the `check_conda_env_torch` touchpoints adjudicated to 3, not 4 — PR #816's actual diff shows the util+test descriptions were one bullet), the ~19 cheatsheet clusters (+87 lines additive), REFERENCE.md's live-compose subsection + 4 TOC rows, the 2 DOCUMENTATION_OVERVIEW nav rows, the 6 runbook subsections incl. the RESUME_MONITOR
  state-machine lines, and the worktree-procedure Phase-4 subsection; 6 duplicated-heading blocks deduplicated (supersets kept, differing subsections merged); 3 units honestly adjudicated (2 SKIPPED-REWORDED-SURVIVOR where fuller reworded text survives; 1 RESTORED-ADJUDICATED where the guidance survives via an explicit cross-reference to REFERENCE.md's full contract). Validation: `pre-commit --all-files` green, `juniper-check-doc-links` valid across 624 files, full battery 1012 tests OK, AGENTS.md
  header/tree gates green. Main advanced mid-heal (v0.7.0 #845 + release merges #848–#850); the branch merged current main cleanly (sole conflict: automation-owned AGENTS.md header lines).

Both PRs were opened owner-gated (`required_signatures`; no auto-merge) and the owner **merged both on 2026-07-29** (#852 at 03:14Z → `4abf936`, #853 at 03:15Z → `1ca69a2`). Prior in-flood heals #838/#842/#843 remain the first wave; #852/#853 complete the census-driven second wave.

### §2.6 Censusclean statement

Census re-verified after heals — first against the heal branches, then **re-certified on main at `23024f5`** after the owner merged #852/#853 (all 59 combined markers, in one pass):

- **Tests + ci.yml** (`fix/flood-census-c1-tests-restore`, PR #852): all **38** restored-symbol/invocation markers present (20 classes' names, the 13 run_fix/hygiene/execute-seam/sweep method+helper grafts incl. `FAILED_PUBLISH_RUN`, and the 4 battery invocations); diff vs the pin is +2045/−0.
- **Docs** (`fix/flood-census-c2-docs-restore`, PR #853): **21/21** finding markers accounted — 20 literal + 1 adjudicated-equivalent (the cheatsheet's `graceful_stop` tip restored reworded, with the full contract present at `docs/REFERENCE.md:225`); runbook `RESUME_MONITOR` mentions = **5**, exactly the §2.3 reconstruction target.

Post-pin main movement (v0.7.0 #845, release-train merges #848–#850/#858, and the heal PRs themselves) is outside the pinned census universe. With #852 and #853 merged and every marker re-verified on main, the pinned window's damage account is **CLOSED — censusclean holds on main** (`23024f5`, runbook RESUME_MONITOR = 5, both dedup targets single).

---

## §3 Guardrail proposals (Task 3) — three independent, validated

Each proposal was drafted blind to the others by an independent agent, then reviewed by three independent validators — (a) an adversarial hallucination/fact refuter, (b) a Juniper-conventions correctness reviewer, (c) an effectiveness reviewer — with at most two revise-and-revalidate cycles. All three proposals reached PASS with **zero unresolved disputes**. Validation records in §3.5.

### Proposal P1 — Repository-side GitHub controls

**Scope:** repository-side GitHub controls only (rulesets, merge settings, bypass actors, app access,
native alarms). RETURN-FINDINGS; the owner decides and performs every change.

**Root cause (drives every recommendation):** the damage was authored by the owner's manual web "Update
branch" 3-way merges (main → stale `cursor/**` branch, then merge), NOT by apps merging. `strict=false`
validated checks on each branch's own last run, never on the fused merge result. The load-bearing control
is therefore "run the real checks on the true merge result — and PERFORM that merge cleanly — before it
lands," plus "stop feeding ~50 concurrent same-file PRs into a manual serial merge."

**Verified live state (probed this session):**

- Ruleset `juniper-ml-rules` id **13805432**, `enforcement=active`, targets `~DEFAULT_BRANCH` (main only;
  `cursor/**` untargeted). `strict_required_status_checks_policy=false`.
- **No `merge_queue` rule; no `pull_request` (required-review) rule** → CODEOWNERS (`* @pcalnon`) is
  advisory only (auto-requests review, does not block).
- **13 authoritative required checks:** Pre-commit ×3, Regression Tests ×3, Build and Validate Package,
  Documentation Links, Security Scan, Quality Gate, Analyze (python), Dependency Documentation,
  Release-Train Archive Guard. `Claude.yml Access Audit` runs on CI but is NOT required (re-verified).
- Bypass actors (all `bypass_mode: always`): `DeployKey`, `RepositoryRole 5` (=admin=owner), `Integration
  1210556`=**cursor**, `1236702`=**claude**, `1276151`=**UNRESOLVED** (needs owner UI verification).
- Merge settings: `allow_auto_merge=true`, `allow_update_branch=false`, all three merge methods on,
  `delete_branch_on_merge=true`; repo **public / User-owned**; classic branch protection 404 (ruleset
  only). **Open PRs now: 0** — this proposal is PREVENTIVE, not backlog-clearing.

**§1 Merge queue vs `strict=true`.** Both implement **M2** (test the prospective merge result). The queue
also implements **M1** (it *performs* a clean automated 3-way merge-or-eject, replacing the owner's manual
Update-branch that authored the damage), so they are NOT equivalent.

- **Prerequisite (MUST wire before enabling — verified gap: zero workflows subscribe to `merge_group`):**
  add a `merge_group:` trigger to **ci.yml** and to **codeql.yml** (a separate, merge_group-blind workflow
  today) and reconcile the PR-only `release-train-archive-guard` job (`ci.yml:423`, `if: pull_request`) —
  else no required context posts, the merge candidate never turns green, and the queue **stalls every
  merge** including the hands-free archive-PR exemption. Re-cost: one-time multi-file wiring + real stall
  risk; **NOT "low cost" until wired.**
- **Availability caveat:** GA docs scope the queue to public repos (and org Team/Enterprise); this repo is
  public but User-owned — the one nuance unconfirmable by read-only API. **Verify in UI** ("Require merge
  queue" selectable?); if not, fall back to `strict=true`.
- **Standing latency tax:** between storms the queue serializes every merge (full 13-check + CodeQL per
  merge, one at a time). Benefit is storm-concentrated.
- **Bypass interaction (honest):** both queue and strict rules are skipped by `bypass_actors`, but apps
  never self-merge — the owner merges everything — so the queue's teeth come from the owner routing every
  merge through "Merge when ready," not from bypass state.

| Incident | Damage | strict=true (M2: re-test the manual merge result) | Merge queue (M1 clean-merge-or-eject + M2) |
|---|---|---|---|
| **#751** (member of the 23:01Z batch) | conflict-res → empty always-pass stub + NameError | **PREVENTED** — NameError → Regression Tests red (a stub-only-if-green portion would slip) | **PREVENTED** — conflict → eject; NameError red |
| **#729** | helper deleted, callers survive; byte-identical dup members | **PREVENTED** — caller breakage → import/test red | **PREVENTED** |
| **#759** | union of two green branches not black-clean → main red | **PREVENTED** — black red on the fused commit (archetypal M2 case) | **PREVENTED** |
| **#738** | fused two same-purpose helpers + silently dropped a sibling test block | **PARTIAL** — fusion red; the silent deletion still passes green | **PREVENTED (full)** — clean auto-merge preserves main's test block; a real drop → conflict → eject |
| **#782** | on-branch class fusion → F821 | **PREVENTED** — F821 red; the branch can't reach green | **PREVENTED** |
| **#801** | docs wholesale-section deletion (AGENTS/REFERENCE/cheatsheet) | **NOT PREVENTED** — manual update re-authors it; prose deletion is invisible to doc-links → green | **PREVENTED** — M1's clean merge keeps main's sections; a genuine conflict ejects, never silently green |
| **#803** | repeat of #801 | **NOT PREVENTED** (same) | **PREVENTED** (same as #801) |
| **23:01Z batch merge** (#744/#751/#739/#753; healed by owner #842) | silent multi-test loss in a ~90 s batch; flake8/mypy/pre-commit all green | **PARTIAL/NOT** — manual batch re-authors; fewer tests still pass green | **PARTIAL** — M1 prevents the manual-merge-authored losses; branch-authored test deletion is the residual |

- **Net (premise: all merges route through the queue):** queue prevents **~7.5/8**, strict=true **~5/8**.
  M1 kills the #801/#803/#738 manual-merge-authored deletion class that strict's re-test cannot (prose/test
  deletion is invisible to linters, so strict sees a *green* merge result). **Conditional (honest):** holds
  under §1's census that damage was authored in the manual merge, not on the branch; the true residual is
  **branch-authored silent test weakening/deletion** (§2's target). The #729 dup-member catch is **mypy
  no-redef**, not flake8 (flake8 ignores F811 at `.pre-commit-config.yaml:129`).

**§2 Required-review (`pull_request`) rule.** WEAK for a solo maintainer: GitHub forbids self-approval, so
on the owner's OWN PRs the requirement is unsatisfiable → falls back to admin bypass; on fleet PRs (app
author) the owner can approve. Advisory under owner-bypass; automates nothing. Value: (a) makes CODEOWNERS
block not merely request; (b) the sole lever at the branch-authored silent-weakening residual, via owner
diligence, zero automation; (c) gives a supervisor a `review_decision` state. **House-fact cost (NIT-1):
it breaks the release-train archive PR's hands-free auto-merge** (App-token author can't self-approve).
Rank optional/last; do NOT remove owner bypass to give it teeth (self-lockout).

**§3 Bypass removal — defense-in-depth, NOT a queue prerequisite.** Removing Cursor's bypass has **zero**
flood-mechanics impact (PR creation isn't a push to main; `cursor/**` refs aren't targeted) and ~0 workflow
cost; it closes the latent app-self-merge-direct-to-main hole. Kills 0 incidents on its own (the incidents
were owner-authored).

| Bypass actor | Identity | Recommendation |
|---|---|---|
| `Integration 1210556` | **cursor** (verified) | **Remove.** No cost; the app never needs to bypass main. |
| `Integration 1236702` | **claude** (verified — the Claude GitHub App) | **Remove.** Same reasoning; `claude.yml` posts comments/commits via PRs, not by bypassing main. Owner should smoke-test @claude on a scratch PR after removal to confirm no regression. |
| `Integration 1276151` | **UNRESOLVED** — id→slug needs the app's JWT (401). **Needs owner UI verification:** Settings → Rules → `juniper-ml-rules` → the Bypass list renders app **names** (not just IDs); or Settings → GitHub Apps / Integrations shows installed apps. | Identify first, then **remove its bypass** unless it is a deliberate automation that must write to main. |
| `RepositoryRole 5` | **admin = the owner (pcalnon)** | **KEEP.** Removing owner bypass + `required_signatures` + a review rule = solo-maintainer self-lockout (can't self-approve, could be blocked on emergency direct-to-main fixes and on the release-train archive/ceremony flows). House fact: owner merges everything. The owner's control is *discipline* (route merges through the queue), not removing their own bypass. |
| `DeployKey` (actor_id `null`) | A category bypass for deploy keys. The concurrency memory notes SSH-key pushes are NOT bypass actors for branch deletion, suggesting no automation relies on a deploy-key bypass to main. **Needs owner verification** of whether any deploy key pushes to main. | **Remove** unless a specific deploy-key automation writes to main. Low cost, closes another direct-to-main hole. |

**Consequence to name (V1a-3):** once the app bypasses are removed, the ceremony's archive PR must **PASS**
(not bypass) all 13 checks — a valid notes-only, add-only archive PR should pass (the Archive Guard is
designed for exactly that shape), but hands-free auto-merge now waits on CI. `required_signatures` and the
`pypi` environment gates are untouched.

**§4 Auto-merge / Update-branch.** Keep `allow_auto_merge=true` but rely on it only behind the queue (or
strict); do not batch-auto-merge stale branches under strict=false. Keep `allow_update_branch=false`
(turning it ON would encourage the hazard). **Honest limit: NO repo setting removes/disables the manual
"Update branch" button** — the only way to retire the hazard is a workflow change (route through the
queue's M1), not a toggle.

**§5 Open-PR budget alarm.** GitHub has NO native "max open PRs" setting and NO built-in open-PR-count
alarm. Recommended: a scheduled Actions workflow (`gh pr list` count → Slack via the existing
`SLACK_WEBHOOK_URL`), **matching the strictly-non-blocking contract** (`continue-on-error:true` +
skip-if-secret-unset; release-train.yml:325-366). Kills 0 directly; attacks root-cause velocity.

**§7 Recommended minimal set (ranked; adoption order is preference, NOT a dependency chain — SF-2):**

1. **Add a merge queue on main (flagship)** — verify UI, else `strict=true` fallback; prerequisite: wire
   `merge_group:` first. ~7.5/8.
2. **Remove the three Integration bypasses** + review DeployKey; keep owner bypass. Defense-in-depth, ~0
   cost.
3. **Add an open-PR budget alarm** (Slack, non-blocking).
4. **Decide the source-control lever** (restrict Cursor app access or a `cursor/**` ruleset — the only
   intake cap).
5. Optional/last: a **required-review rule** (only if the owner will read every fleet diff).

| Control | Exact setting / API surface | Incidents killed | Cost to solo-maintainer + fleet flow | Recommendation |
|---|---|---|---|---|
| Merge queue on main | Ruleset → Add rule → "Require merge queue"; **prerequisite:** add `merge_group:` to ci.yml + codeql.yml, reconcile `release-train-archive-guard` `if` (ci.yml:423); owner uses "Merge when ready" | **~7.5/8** — #751/#729/#759/#782/#801/#803/#738 + batch partial (M1 clean-merge-or-eject + M2) | One-time multi-file wiring + stall risk if mis-wired; standing per-merge latency tax; owner must stop manual Update-branch | **Adopt if available (flagship; verify UI)** |
| `strict=true` (fallback) | Set `strict_required_status_checks_policy=true` in `required_status_checks` | **~5/8** — #751/#729/#759/#782 + #738 partial; **misses #801/#803/batch** (M2 only; the update is still the manual 3-way merge) | **High** — O(N²) Update-branch thrash at ~50 PRs; update is still a manual 3-way merge | **Only if queue unavailable (honestly weaker)** |
| Remove Integration bypasses | Ruleset 13805432 → Bypass list → delete 1210556 / 1236702 / 1276151 (+ review DeployKey). Keep RepositoryRole 5. | 0 directly; **defense-in-depth** for the hypothetical app-self-merge path (NOT a queue prerequisite) | ~0 (apps don't self-merge); archive PR must then pass (not bypass) the 13 checks (V1a-3) | **Adopt (cheap hygiene)** |
| Open-PR budget alarm | New scheduled `.github/workflows/*.yml`: `gh pr list` count → Slack (`SLACK_WEBHOOK_URL`, `continue-on-error:true` + skip-if-unset) / tracking issue | 0 directly (root-cause velocity) | ~0; one small workflow; already-patterned | **Adopt** |
| Block/scope Cursor at source | Settings → GitHub Apps → Cursor → Repository access (remove juniper-ml), OR a `cursor/**` ruleset with creation/update restriction | Prevents the flood entirely (all classes, by stopping intake) | High social cost — disables the fleet's value on this repo; owner's call | **Owner decision (v)** |
| Required-review rule | Ruleset → Add rule → "Require a pull request before merging", `required_approving_review_count:1`, `dismiss_stale_reviews_on_push:true`, opt. `required_review_thread_resolution` | Only the branch-authored silent-weakening residual, via owner reading diffs — 0 automatic | Advisory under owner-bypass; blocks owner's OWN PRs (no self-approval); **breaks archive-PR hands-free auto-merge (NIT-1)** | **Optional / last** |
| Auto-merge policy | Keep `allow_auto_merge=true`, use only behind the queue; keep `allow_update_branch=false` | 0 alone; removes the manual-batch race (23:01Z-batch class) behind the queue | ~0 | **Adopt behind queue** |

**Do NOT:** remove the owner's RepositoryRole 5 bypass; turn ON `allow_update_branch`; touch
`required_signatures` or the `pypi` environment gates.

**Unverified / flagged for owner:** merge-queue availability on a User-owned public repo (verify UI);
merge_group required-context behaviour after wiring (smoke-test a scratch queued PR); Integration 1276151
identity; DeployKey-to-main usage; the "no setting disables the Update-branch button" fact (load-bearing,
minor UI-visibility rules not exhaustively verified); the M1 re-scoring's conditional (those deletions
authored in the manual merge, not independently re-diffed per-incident); incident counts (134/133/125/
136-carrier) cited from the census — batch-member timestamps WERE verified this session.

Full validated text: developed under the program's validation pipeline; decision tables above are verbatim.

---

### Proposal P2 — Compositional CI: sequence-safety gates

**Scope:** CI-layer designs for later owner-merged PRs; read-only + `gh api` GET, no code shipped here.

**Root cause (grounded):** damage was **compositional** — every PR was individually green; serial same-file
merges into main fused/deleted sibling content; a deleted test cannot fail, so flake8/mypy/pre-commit
stayed green. Ruleset 13805432 `strict=false`, no `merge_queue`, `bypass_mode=always` for owner + Cursor
App → required checks **inform, they do not enforce**; every per-PR gate below is **advisory for exactly the
two actors that caused the damage** (owner + Cursor). Reconstruction fact: every merged PR tip survives as
`<merge>^2`; the last-good main-side blob is `<merge>^1`.

**Incident-class → gate map (recalibrated):**

- **(a) Silent symbol deletion** (a def present at base, gone at head, leaving no error): #1(`#751`),
  #4(`#738`), bulk of #7(`#744`/`#739`/`#753`/`#755`) → **G1 + G3** — their *unique* value (nothing else in
  CI sees a clean deletion).
- **(b) Fusion** — dup member/redef #2(`#729`, mypy `no-redef`) or wrong attribute #5(`#782`, mypy
  `attr-defined`) → **already netted by the REQUIRED pre-commit mypy** (flake8 ignores F811 at `:129`);
  G1/G3 coverage is best-effort overlap only, uncertain (on-branch fusion looks like additions from main's
  first-parent view).
- **Docs section deletion** #6(`#801`/`#803`) → **G2 (+ G3 step 4)**.
- **Pre-commit merge-ref contamination** from union-non-clean main #3(`#759`) → **G4**.

**Wiring requirement (do not skip):** `ci.yml`'s `tests:` job runs an explicit enumerated `unittest` list
(`ci.yml:128-399`) — no pytest auto-discovery — so each new lint-test (`tests/test_symbol_loss_check.py`,
`tests/test_docs_additions_check.py`) MUST be added to that battery AND to AGENTS.md's run-all list in the
same PR, or it ships **silently dead**. The census tooling exists only as **untracked** ad-hoc
(`util/ad-hoc/2026-07-28_flood_census_*.py`); productionization must land it in-repo under
`util/sequence_safety/` — citations are provisional until then.

**G1 — symbol-loss gate (per-PR).** On `pull_request`, build an AST symbol inventory for each in-scope file
at the **base** and at the **merge ref** (`refs/pull/N/merge` = true post-merge composition), FAIL on
`LOST`/`WEAKENED`/`DUPLICATED` unless declared; reuse the archive-guard base-diff recipe (`ci.yml:429-452`;
three-dot inside `archive_guard.py:224-230`).

- **Scope (resolved):** top-level `tests/*.py` + `util/**` (census `in_scope`, `symbol_screen.py:37-43`);
  excludes `scripts/`, sub-package `src`, nested `tests/*/`.
- **Escape hatch:** commit trailer `Allow-Symbol-Loss: <qualified.symbol>[,...]` (primary, auditable,
  post-merge-visible, must enumerate — no wildcard) + PR label `allow-symbol-loss` (made
  enumerated-or-WARN-only, never a blanket per-PR waiver).
- **FP handling:** downgrade `LOST`→`RELOCATED` (WARN) only on a *qualified-name* match or body-similarity,
  never a bare name (test files reuse `setUp`/`test_default` → false-negative in the exact damage locus).
- **Required-check decision: runs STANDALONE**, NOT in the Quality-Gate `needs:` (`ci.yml:664`) — QG is
  `if: always()` + required, so a skipped PR-only job would fail every `push:main`; mirrors the
  `release-train-archive-guard` precedent. Soak advisory first (codeql `:15-17` convention), promote to
  required **later, directly in the ruleset**, never via the QG `needs:`.
- **Build MED / Run LOW.** Kills #1/#4/#7 (silent deletion); #2/#5 best-effort (mypy is the primary net).

**G2 — docs additions-only gate (docs-class PRs).** `git diff --merge-base FETCH_HEAD HEAD -- <docs
cluster>`, **magnitude-gated** (not any-minus-line ⇒ FAIL): **FAIL** on a deleted Markdown heading OR a run
of **≥ N consecutive deleted lines** (default N=8, owner-tunable); **WARN** on small in-place swaps.

- **Scope:** DOC_UNION_6 (`AGENTS.md` + `CLAUDE.md` symlink, `docs/**`, and the 2 churned `notes/`
  runbooks). **Residual (honest):** only 2 `notes/` files pinned; every other `notes/**` is uncovered.
  Widen option: all `notes/**` + `docs/**` + top-level `*.md` (higher FP; leans harder on the threshold +
  `docs-rewrite` label). Recommend narrow, widen a file on first churn.
- docs-class iff *every* changed file is docs/`.md`; mixed feature PRs are out of scope (optional
  non-blocking annotation on their doc-cluster minus-lines). This is the one class CI could not previously
  see: doc-links only catches dangling anchors, never prose/section deletion.
- **Build SMALL / Run LOW / FP LOW.** Kills #6, reinforced post-merge by G3 step 4.

**G3 — post-merge main-verification (the bypass-proof net).** New `.github/workflows/main-verification.yml`,
`on: push: branches: [main]` — fires no matter who merged or bypassed (the only gate the always-bypass
actors cannot skip). Steps: (1) `symbol_loss_check.py --base <before> --head <sha>`; (2) full unittest
battery (factor into a shared `scripts/run_regression_battery.bash`); (3) `pre-commit run --all-files`
(the global union check); (4) **docs magnitude-deletion screen** (G2 logic post-merge) — **without step 4,
G3 has no docs net at all, and #6 is exactly the class that recurred.**

- **Concurrency (grounded fix):** `ci.yml:41-43` uses `group: ci-${{ github.ref }}, cancel-in-progress:
  true`; for main pushes `github.ref` is constant, so rapid serial merges **cancel each other** — during a
  storm only the last merge's run survives. G3 MUST use per-SHA `group: main-verify-${{ github.sha }},
  cancel-in-progress: false` so **every** merge is verified.
- **Notify (loud):** issue upsert (`issues: write`) + Slack (`SLACK_WEBHOOK_URL`, non-blocking,
  release-train.yml:325-366).
- **Build MED / Run HIGH (dominant cost).** **Burst caveat:** per-SHA no-cancel launches concurrent
  batteries → runner-cap/queue delay (delayed, not dropped). Mitigation (a) always run the seconds-screens
  and gate the full battery behind `tests/`|`util/`-touched; recommend (a). Kills **all compositional
  classes as a post-merge net**.

**G4 — pre-commit merge-ref contamination remedy.** CI runs `pre-commit run --all-files` on the merge ref
(`ci.yml:90`), so when main briefly carried a union-non-clean file (#3/`#759`), **every** open PR went red
regardless of its own content. Split: **PR CI** scopes to the PR's own changes
(`pre-commit run --from-ref origin/${{ github.base_ref }} --to-ref HEAD`); **main-push/G3** keeps
`--all-files`. The union-in-untouched-file residual is covered by G1/G3. **Build SMALL / Run LOWER than
today / FP low.** Kills #3.

**§6 Ranked recommended subset (build order):**

1. **G1 module + G3 post-merge screen** — the silent-deletion net; bypass-proof at G3; highest severity.
2. **G4 pre-commit changed-files split** — tiny edit, kills the highest-blast-radius class (#3). Cheap win.
3. **G1 per-PR check + G2 docs additions-only** — pre-merge advisory signals (soak non-required, then
   promote).
4. **G5 (i) queue meter, (iv) fleet-PR lint, (vi) supervisor artifact** — incremental observability.
   **G5 (ii) strict/merge-queue and (v) remove Cursor bypass are RULESET/repo-control fixes, not CI —
   escalate to owner as the true systemic remedy.**

| Gate                       | Trigger                           | Incidents killed                                                         | Build cost | Run cost                           | False-positive risk                                      |
|----------------------------|-----------------------------------|--------------------------------------------------------------------------|------------|------------------------------------|----------------------------------------------------------|
| G1 symbol-loss (per-PR)    | `pull_request` (merge ref)        | #1,#4,#7,#755 (silent deletion); #2,#5 best-effort (mypy is primary net) | MED        | LOW                                | MED → enumerated trailer (label enumerated or WARN-only) |
| G2 docs additions-only     | `pull_request`, docs-only PR      | #6 (#801,#803)                                                           | SMALL      | LOW                                | LOW (magnitude threshold + `docs-rewrite` label)         |
| G3 post-merge main-verify  | `push:main` (+issue/Slack notify) | all classes as post-merge net (incl. docs via step 4)                    | MED        | HIGH (battery×merges; burst→queue) | LOW (advisory notify)                                    |
| G4 pre-commit split        | `pull_request` vs `push:main`     | #3 (#759)                                                                | SMALL      | LOWER than today                   | LOW (union-in-untouched → G3)                            |
| G5(i) queue meter          | `pull_request`/schedule           | prevention/visibility                                                    | SMALL      | LOW                                | n/a advisory                                             |
| G5(iv) fleet-PR lint       | `pull_request`                    | best-practice                                                            | SMALL      | LOW                                | MED (scope not machine-declared)                         |
| G5(vi) supervisor artifact | `pull_request`                    | observability                                                            | SMALL      | LOW                                | n/a                                                      |

**Non-goals:** not enforcing merge freshness in the CI layer (that is ruleset `strict`/`merge_queue`); not
modifying ruleset 13805432 or its bypass actors (recommended to the owner, not a CI artifact); not
auto-closing Cursor PRs from CI (unreliable vs the App's always-bypass); not a semantic-equivalence checker
— **`WEAKENED` is bounded** (`cur_lines ≤ 0.6·max_prior_lines` AND Δ ≥ 4, `symbol_screen.py:33-34,303`), so
a **same-length gutting (Δ=0)** is invisible to it (needs mypy/human review); not covering non-`.py`/`.bash`
/docs content; not a replacement for human review.

**Open questions / unverified:** escape-hatch canonical (recommend both, trailer primary, label
enumerated-or-WARN-only); promote G1/G2 to required now vs soak (promotion in the ruleset directly, never
via QG `needs:`); G3 full-battery-every-merge vs battery-only-when-`tests/`|`util/`-touched; G2 narrow
DOC_UNION_6 vs all `notes/**`; symbol scope decided (census `in_scope`, widen later if damage recurs);
enable `merge_queue`/`strict`/drop Cursor bypass. **[ASSUMPTION]s flagged:** `pull_request` runs on merge
ref `refs/pull/N/merge`; `github.event.before == <merge>^1` on non-ff merges (`HEAD^1` fallback);
`pre-commit --from-ref/--to-ref` scopes to changed files; `workflow_run` fires on ci.yml completion — none
independently re-verified in-repo this session.

Full validated text: developed under the program's validation pipeline; decision tables above are verbatim.

---

### Proposal P3 — Supervisory layer + fleet policy

**Scope:** supervisory layer + fleet policy; RETURN-FINDINGS, no repo mutation; the owner decides.

**Grounding (verified this session):**

- Ruleset `13805432` governs `main` ONLY (`include=["~DEFAULT_BRANCH"]`); `cursor/*` branches ungoverned.
  No `merge_queue`, no `pull_request` rule. `strict_required_status_checks_policy=false` — CI runs on the
  branch head, never the merge result (the exact hole); 13 required contexts.
- Bypass actors (all `always`): `DeployKey`, **`RepositoryRole 5` (admin=owner — load-bearing: the owner
  can click-merge past every non-nuclear stage)**, `Integration 1210556` (Cursor App), `1236702`,
  `1276151`. Merge settings: `allow_auto_merge=true`, `allow_update_branch=false`.
- Docs (`AGENTS.md`/`REFERENCE.md`/cheatsheet) have **only** markdownlint + dangling-anchor check → prose/
  section deletions have **no** gate.
- **Suite auto-adoption:** a new `fleet-supervisor.md` is auto-mirrored, auto-doctored, and
  auto-frontmatter-gated (`test_agents_frontmatter.py` requires `model: opus` + `effort: max`) the moment
  it lands.
- **Storm shape (re-derived, cursor-merge-scoped):** 2026-01:0, 02:0, **03:43**, 04:0, **05:10**, 06:0,
  **07:129** — **bimodal, two bursts months apart, NOT a steady monthly cadence.** Phase-0's 47/10/28/130
  NOT reproduced except 05(10): 07 ≈ reproduces (129 vs 130); 03 differs (43 vs 47); **06 does not reproduce
  (0 vs 28 — June had 4 total main merges, none cursor)**. Open-PR count now **0** (a drained trough).

**§1 Supervisory layer — deterministic SCRIPT + O(1)/batch AGENT (V3c-E1 restructure).**

- **(1A) `util/fleet_triage/predict_merge.py`** (gated by `tests/test_predict_merge.py`): per PR, in a
  throwaway **detached `git clone`** (NOT `git worktree add`, never the owner's checkout, never a push),
  `git merge --no-ff origin/main` into the branch tip, then on the RESULT run repo-pinned fast gates on
  touched files (`pre-commit run black isort flake8 mypy check-ast --files <changed>`; black 26.3.1, mypy
  v1.13.0, check-ast `:83`) **plus two screens CI cannot see** — an AST **symbol screen** (LOST-vs-main =
  the #755/#729/#738 class mypy/flake8 pass) and a docs **additions-only screen** (`git diff origin/main
  <result> -- <docs>`; any `-` = suspected #801/#803 section deletion). Emits per-PR JSON incl. the **TRUE
  changed-file delta** (`git diff --name-only origin/main...<result>`). Seconds/PR, no agent, re-runnable.
- **(1B) `.claude/agents/fleet-supervisor.md`** (read-only; tools `Read,Grep,Glob,Bash`; opus/max;
  findings-as-message — the `mock-seam-auditor` precedent): invoked **once per batch**, reads the script
  JSON to adjudicate dup/supersession, build the cluster map, compute the stale-minimizing merge **order**,
  and emit per-PR verdicts + an ordered plan with "re-run `predict_merge.py` after this merge" checkpoints —
  **O(1) opus/max per batch**, not ~125 invocations. Any headless commit uses `-c commit.gpgsign=false`.

**Cost model (honest):** mypy dominates (~15-30s cold per `.py` file; a docs-only PR skips mypy → ~1-2s).
**T0** ≈ 125 PRs × ~20s ≈ 2,500s (~42 min) serial worst-case; realistic **minutes** (July is docs-heavy:
64/135 window merges touch `.md`), trivially parallelizable. **Per-merge re-validation** of a same-file
cluster of size k = k(k-1)/2 script re-runs; the four hot clusters are ALL docs (AGENTS.md **54**, cheatsheet
**53**, runbook **34**, REFERENCE.md **15**) → sub-second additions-only screens; the mypy-bearing cost lands
only on the ≤12-PR `.py` clusters (top-5 ≈ 247 re-runs ≈ 82 min serial; summing all 33 `.py` clusters ≈ 311
≈ 104 min worst-case, far less in practice — per-file scope, only still-open PRs, parallel, warm cache).
**Agent: one** opus/max invocation per batch.

**Dup/supersession (V3c-E3 — corrected mechanism):** `detect.py`'s `has_substantive_hunk`/
`substantive_between` are single-file base-vs-head classifiers and cannot compare two PRs. Real mechanism:
per-PR **normalized added-line multiset per file** from the predicted-merge delta; **dup-SUSPECT** on
Jaccard/containment over threshold. Near-dup **titles** with disjoint content (**#772 vs #774**, both
genuine) score LOW, not flagged. **Two-key DUP-CLOSE** (a false close = LOST REAL WORK): requires BOTH high
overlap AND the agent's judgment + **owner confirmation**; the script never auto-closes.

**The four verdict classes:** **MERGE-CLEAN** (result conflict-free, gates pass, no lost symbols, docs
additions-only); **NEEDS-UPDATE-BRANCH** (behind main; needs a **rebase**, never a union/take-own-side merge
— that created #751); **DAMAGED-FIX-FIRST** (result fails a gate / lost symbol / deleted docs section —
**flags** #738/#751/#782/#801; a read-only gate can flag a bad human conflict-fix, not validate one);
**DUP-CLOSE** (recommend close, owner-confirmed only). The cluster map is built from the script's TRUE deltas,
NOT `gh pr list --json files` (which showed 12 files vs 2 truly changed for #729). Gating tests
(`test_predict_merge.py`, `test_fleet_supervisor_contract.py`) MUST be wired into the ci.yml enumerated
battery + AGENTS.md run-all; adoption co-changes AGENTS.md (agents-list node, tests bullets, run-all lines,
`util/fleet_triage/` tree entry).

**§2 Cursor-dashboard controls to request (owner performs; ALL "verify in dashboard", none assumed):**
concurrency cap (≤ owner triage rate, e.g. ≤5); schedule cadence (throttle the bursts); per-class disjoint
file scopes (docs automation owns `docs/**`+`AGENTS.md`, test automation owns `tests/**`); per-run PR budget;
draft-PR creation (feeds Stage 2); target-branch selection (feeds Stage 2); automation count (ml#844 body
says 3, the 2026-07-26 note lists 4 check names).

**§3 AGENTS.md "Third-Party Agent PR Contract" (paste-ready ~20 lines; insertion `###` under `## Pull
Request Conventions`, AGENTS.md:640):** 8 rules — (1) one tidy commit; (2) run the repo-pinned formatters
before push; (3) dup-guard first via `gh pr list` (#772 vs #774 title exception); (4) no same-file fan-out
beyond declared scope (the ×54/×53/×34 pile-up); (5) docs changes additions-only unless labeled
`docs-rewrite` (#801/#803 class); (6) declare touched-file scope in the PR body; (7) branch naming
`cursor/<automation>-<slug>`, one purpose; (8) stale-branch policy = **rebase**, never union-merge/
take-own-side (authored #751/#738/#782). **Enforceability caveat:** whether Cursor reads repo `AGENTS.md` at
generation time is **unverified (OQ3)** — otherwise the contract is enforced only by the supervisor at
review time.

**§4 The blocking option, evaluated honestly.**

| Mechanism | Owner-level? | Stops PR creation? | What it actually does |
| --- | --- | --- | --- |
| **Remove Cursor (Integration 1210556) from ruleset bypass** | Yes (ruleset edit) | **No** | PR creation is not a `main`-ref op, and `cursor/*` branches are ungoverned (`include=["~DEFAULT_BRANCH"]`). Cursor doesn't self-merge; the owner (admin bypass) does. **Near-zero flood effect alone.** Its only real use: a **prerequisite** for a merge queue / strict policy to gate Cursor's PRs (bypass actors skip a queue). |
| **Enable `strict_required_status_checks_policy: true`** | Yes (one ruleset setting) | No | Forces every PR up-to-date + re-checked on the merge base before merge → **detects** the stale-branch union class (#759/#738). But **RepositoryRole-5 admin bypass still lets the owner click merge past it** — so it informs, it does not bind the owner-batch-merge class. |
| **Add a `merge_queue` rule** (+ remove Cursor bypass) | Yes | No | GitHub-native equivalent of the script's predicted-merge: validates the actual merge result before landing, and (unlike strict) a queue **binds** even the owner unless bypassed. ml#844's recommended systemic fix. Requires bypass-removal to bite. |
| **Restrict the Cursor App's repository access** (remove juniper-ml from its selected repos) | Yes — GitHub App *installation* settings (`github.com/settings/installations`), **not** a ruleset, **not** the Cursor dashboard | **Yes, for juniper-ml only** | The surgical lever: Cursor keeps working elsewhere, stops opening PRs here. |
| **Uninstall the Cursor GitHub App** | Yes | **Yes, everywhere** | Nuclear; loses the tool account-wide. |
| **Revoke the app's `pull_requests: write` permission** | No — app-developer (Cursor) side | n/a | Not an owner lever. |

**Key honest finding:** removing the ruleset bypass does **not** stop the flood; only restricting/
uninstalling the app's *access* does. The ruleset is the right tool for "validate the merge result" (strict/
merge queue), the wrong tool for "stop PR creation." Binding gap: strict-checks and every supervisor stage
below a merge queue (Stage 1-alt/2) or blocking (Stage 3) leave the RepositoryRole-5 admin-batch-merge path
open.

**Staged adoption path:**

- **Stage 0 — Advisory supervisor (RECOMMENDED START):** zero GitHub/Cursor config change; owner runs
  `@fleet-supervisor` before each merge batch. **This DETECTS the incident families; it PREVENTS nothing by
  itself** — prevention is contingent on the owner (a) running it per batch, (b) acting on verdicts, (c)
  re-running the script pass between merges instead of batch-clicking. **Entry:** agent + `predict_merge.py`
  + both gating tests merged & wired. **Exit→1:** verdicts match post-merge reality across ≥2 batches, AND
  no batch was merged without a report / the per-merge script pass, AND the post-merge screen finds no
  missed damage.
- **Stage 1 — + strict checks (or merge queue):** flip `strict=true` (one setting) or add `merge_queue` +
  remove Cursor bypass; the supervisor supplies the cross-PR dup/cluster/order intelligence GitHub cannot.
  *Strict still does not bind the admin-batch path; a merge queue does.* **Exit→2:** fleet volume exceeds
  triage capacity, or union damage recurs despite strict.
- **Stage 2 — Draft-only / integration-branch fleet:** Cursor emits drafts or targets `fleet/incoming`
  (OQ2); the supervisor promotes validated ones. **Exit→3:** drafts still collide, or owner wants full
  mediation.
- **Stage 3 — Full mediation (blocking):** remove juniper-ml from Cursor App repo access; fleet arrives as
  branches/patches. **The supervisor plans and validates; it NEVER authors or pushes — the consolidated PRs
  are authored by a `task-executor` agent or by the owner.** Concentration risk: consolidating same-file PRs
  is itself the fusion-prone operation (#738/#782); mitigation = every consolidated result runs the SAME
  gate battery, batches kept small. **Exit:** terminal (revert by re-granting access).

**§6 Recommendation + measures table. Recommended start: Stage 0 (advisory supervisor) + Stage 1's
one-setting strict flip in parallel.** Both DETECT; **neither BINDS the owner's admin-batch-merge path** —
that binds only at a merge queue (Stage 1-alt/2) or blocking (Stage 3). Escalate only if damage recurs
(blocking costs Cursor's self-healing #800 + concentrates risk on the supervisor).

| Measure | Mechanism | Detects | Prevents (contingent) | Owner effort | Risk |
| --- | --- | --- | --- | --- | --- |
| Advisory supervisor (Stage 0) | script predicted-merge + agent dup/cluster/order | #738 #751 #759 #729 #782 #801 #803 #755 (all 8) | none by itself — contingent on run-per-batch + act-on-verdict + re-run-between-merges | Med (run script per batch; agent O(1)/batch) | Low (advisory; owner still merges) |
| Strict status checks (Stage 1) | ruleset `strict=true` | #759 #738 (stale-branch union) | contingent — admin bypass still merges past | Low (one setting) | Low-Med (re-check cost) |
| Merge queue (Stage 1 alt) | ruleset `merge_queue` + remove Cursor bypass | all union-merge (#738 #759 #729 #751) | **yes** (binds; validates merge result) | Med (config + workflow) | Med (queue latency; bypass-removal peer effects) |
| AGENTS.md PR contract | §3 paste-in + supervisor enforces | dup fan-out (AGENTS 54 / cheatsheet 53 / runbook 34) + docs deletion (#801 #803) | contingent (only if Cursor reads it — OQ3) | Low (doc) | Low |
| Dashboard caps + disjoint scopes | Cursor dashboard (verify) | excessive-queue (bursts) + same-file pile-up | **yes at source** (if Cursor supports it) | Low (dashboard edits) | Med (unverified Cursor capability) |
| Block repo access (Stage 3) | remove juniper-ml from app install | all fleet-origin incidents | **yes** (no PRs created) | High (loses Cursor iteration) | High (SPOF + consolidation concentration on supervisor) |

**Open questions (owner):** OQ1 automation count (3 vs 4); OQ2 Cursor caps/budget/scope/draft/target
support; OQ3 does Cursor read `AGENTS.md` at generation; OQ4 read-only supervisor vs gated push for
lint-fixes; OQ5 flip `strict=true` now; OQ6 add `merge_queue` + remove Cursor bypass (the only lever that
BINDS the admin-batch class); OQ7 remove Cursor from bypass now (near-zero flood effect alone; sits alongside
1236702/1276151 peers — confirm expectations first); OQ8 archive a durable plan to `notes/` (via `planner`)
or return-as-message only. **Unverified vendor capabilities:** every §2 control + OQ1-OQ2 — the owner
verifies in the Cursor dashboard / GitHub App installation settings; none assumed.

Full validated text: developed under the program's validation pipeline; decision tables above are verbatim.

---

### Cross-proposal comparison

| Control / measure (source) | Layer | Incident classes addressed (with contingency markers) | Owner effort | Build cost | Dependencies / prerequisites | Standalone value |
|---|---|---|---|---|---|---|
| **P1** Merge queue on main [merge_group wiring prereq] | Prevention (merge-time; M1 clean-merge-or-eject + M2 test-result) | ~7.5/8 — #751/#729/#759/#782/#801/#803/#738 + batch partial | Adopt "Merge when ready" as sole path + standing per-merge latency tax | One-time `merge_group` wiring (ci.yml + codeql.yml + archive-guard `if`) | **Step 0:** wire `merge_group` (else stalls all merges); queue availability (verify UI) | High — binds the merge result natively |
| **P1** `strict=true` fallback | Prevention (M2 only) | ~5/8 — #751/#729/#759/#782 + #738 partial; **misses #801/#803/batch** | O(N²) Update-branch thrash at ~50 PRs | One ruleset setting | None | Medium — honestly weaker than the queue |
| **P1** Remove Integration bypasses (+DeployKey review) | Prevention (hygiene) | 0 directly — defense-in-depth for the hypothetical app-self-merge path | ~0 | None | NOT a queue prereq; after removal archive PR must PASS 13 checks | Closes a latent direct-to-main hole |
| **P1** Open-PR budget alarm | Detection | 0 directly (root-cause velocity) | ~0 | One scheduled workflow | `SLACK_WEBHOOK_URL` (skip-if-unset, non-blocking) | Yes — visibility |
| **P1** Required-review rule | Process / detection | Only branch-authored silent-weakening residual, via owner diligence — 0 automatic | Blocks owner's OWN PRs; breaks archive-PR auto-merge | One ruleset rule | Owner reads every fleet diff; keep owner bypass | Weak for a solo maintainer |
| **P1** Block/scope Cursor at source | Prevention (source intake cap) | Prevents the flood entirely (all classes) | High social cost — loses the fleet's value here | App-access edit OR `cursor/**` ruleset | None | Yes — the only intake cap |
| **P2** G1 symbol-loss gate | Detection (pre-merge, merge ref) | #1/#4/#7 silent deletion; #2/#5 best-effort (mypy is primary) | Low (review the red) | MED (lift + reharness + lint-test + job) | Wire lint-test into battery + AGENTS.md; advisory for bypass actors | High pre-merge signal (bypassable) |
| **P2** G2 docs additions-only gate | Detection (pre-merge, docs-class) | #6 (#801/#803) — docs section deletion | Low | SMALL | DOC_UNION_6 scope (2-notes/ residual); wire lint-test | The only pre-merge docs-deletion net |
| **P2** G3 post-merge main-verify [incl. docs screen] | Detection (post-merge, BYPASS-PROOF) | all compositional classes as a post-merge net (incl. docs via step 4) | Low (loud notify) | MED | Per-SHA concurrency fix; shared battery script; Slack/issues | **Highest — the only unbypassable net** |
| **P2** G4 pre-commit changed-files split | Prevention (removes false-red blast radius) | #3 (#759) contamination | ~0 | SMALL | Add base fetch | Yes — cheap win |
| **P2** cancel-in-progress per-SHA fix | Detection-enabler (near-free, high value) | Unblocks G3 storm coverage (else only the last merge is verified) | ~0 | Trivial (one concurrency stanza) | Part of G3 | Near-free structural fix |
| **P3** Stage-0 supervisor (script + agent) | Process / detection | all 8 detected; **prevents nothing without owner adherence** | Med (run per batch; agent O(1)/batch) | predict_merge.py + agent + 2 gating tests + ci/AGENTS.md wiring | Owner discipline; wiring | Yes as a detector (advisory) |
| **P3** AGENTS.md PR contract | Process | dup fan-out + docs deletion — **contingent (only if Cursor reads it, OQ3)** | Low (doc) | Paste-in + supervisor enforces | OQ3 (else review-time only) | Low alone |
| **P3** Cursor dashboard asks | Prevention at source (if supported) | excessive-queue + same-file pile-up — **yes at source (if Cursor supports)** | Low (dashboard) | None (vendor config) | UNVERIFIED Cursor capability (verify dashboard) | Yes at source (unverified) |
| **P3** Staged blocking (Stage 3 app-access removal) | Prevention (full mediation) | all fleet-origin incidents (yes — no PRs created) | High (loses Cursor iteration #800) | App-access removal + task-executor consolidation | Supervisor proven at Stages 0-2; SPOF + consolidation concentration | Yes — terminal |

**Complementarity.** The three proposals occupy different layers and are additive, not competing. **P1
prevents at merge time** — the merge queue's clean-merge-or-eject (M1) performs the merge itself so a
wholesale deletion either merges clean or ejects, never silently green. **P2 detects compositionally, pre-
and post-merge** — and G3 is the *only unbypassable net* given the always-bypass actors (owner + Cursor),
firing on `push:main` no matter who merged or what they skipped. **P3 restores order at the process level** —
triage, merge-order, dup/cluster adjudication, and the AGENTS.md contract. The honest residuals dovetail:
P1's true residual (branch-authored silent test weakening/deletion) is exactly **P2-G1/G3's kill** (the
merge-ref/post-merge symbol screen), leaving only P2's own same-length-gutting (Δ=0) sub-residual for mypy/
human review; P2's "advisory for the two bypass actors" limit is exactly what **P1's queue/strict binds**
(the queue routes the merge; removing bypass makes the required checks enforce); and P3's owner-discipline
dependency (Stage 0 detects but prevents nothing) is precisely what **P1's binding controls remove**.

**Overlaps / tensions.** Three measures all attack the excessive-queue class: P2's G5(i) queue-meter and
P1's budget alarm both *detect* (advisory counts), while P3's dashboard caps *throttle at source* if Cursor
supports them — adopt P1's near-free alarm as the detector and escalate to P3's dashboard caps for real
throttling; they are complementary. The sharpest overlap is P1's queue vs P3's `predict_merge.py`: once a
real GitHub **merge queue is live (Stage 1-alt+), the native queue WINS** for merge-result validation — it
does M1+M2 and *binds* — so the script's predicted-merge becomes redundant *for that purpose* and P3's
supervisor retains unique value only as the cross-PR dup/cluster/**order** intelligence the queue lacks
(P3 says exactly this). **Below Stage 1 (no queue), the supervisor's predicted-merge is the owner's only
merge-result screen.** Note also the strict-vs-queue tension P3 flags: `strict=true` detects but does not
bind the RepositoryRole-5 admin-batch path — only the queue (or Stage-3 blocking) binds it.

---

*Footnote on incident bookkeeping: the proposals' 8-slot incident enumerations differ in one slot's membership (P2 counts #755 as its own class and folds #751 into the empty-stub slot; P1 counts the 23:01Z batch as one slot including #751; P3 lists #755 and #751 separately). The taxonomy in §1(c) has 8 damage classes with overlapping PR membership; each proposal scored consistently against its own enumeration, so kill-claims are per-class and unaffected by the slot bookkeeping.*

### §3.5 Proposal validation records

**P1 — Repository-side GitHub controls (Final: PASS, 1 cycle).** First round: the **refuter PASSED** (all
live-state claims confirmed, including the app-ID resolutions), flagging the #842-as-incident mislabel plus
2 nits. **Conventions FAILED** with a MUST-FIX: no `merge_group` triggers exist, so a queue would stall all
merges including the archive-PR exemption (+2). **Effectiveness FAILED** independently finding the same gap
(MUST-FIX), plus SHOULD-FIX items: the queue was under-scored — its M1 clean-merge-or-eject prevents the
docs-deletion classes — and the bypass-removal ranking was overstated (+2 nits). Revision R1 applied all 11
items with zero disputes. Re-validation **V1′ PASSED**: every cure verified (`merge_group` grep 0-hit,
ruleset contexts exact, batch timestamps to the second), no stale residue, no new defects.

**P2 — Compositional CI (Final: PASS, round 1 + grounded refinement).** First round: the **refuter PASSED**
(the headline cancel-in-progress finding CONFIRMED true; assumptions honest); **conventions PASSED**;
**effectiveness PASSED** with recalibrations (the required mypy already nets the fusion classes; G3 was
docs-blind; the relocation false-negative; escape-hatch tuning). A convergent finding by all three reviewers:
sequence-safety must run **standalone**, not inside the Quality-Gate `needs:`. Revision R2 applied 14 items,
all re-grounded, zero disputes, one transparency softening. **No re-cycle needed** (zero MUST-FIX ever).

**P3 — Supervisory layer + fleet policy (Final: PASS, 1 cycle).** First round: the **refuter PASSED** (every
mechanism/file/GitHub fact confirmed; monthly figures + 2 version cites flagged for sourcing);
**conventions PASSED** (the proposed frontmatter passes the real suite gate; wiring/authorship fixups);
**effectiveness FAILED** with 2 MUST-FIX (the re-validation loop was unpriced/infeasible as an agent-loop;
the advisory-≠-preventive overclaim with adherence unmeasured) plus dup-mechanism, stale-input, and Stage-3
authorship items. Revision R3 applied all 15 with zero disputes, and re-derived the cursor-merge monthly
counts (2026-03:43, 05:10, 06:0, 07:129 — bimodal, correcting the "monthly storm" framing; June-created-vs-
merged bucketing likely explains Phase-0's 28). Re-validation **V3c′ PASSED**: both cures structural, the
cost-model arithmetic independently re-computed, the monthly counts reproduced exactly; one nit (top-5 vs
all-clusters subtotal) was fixed by the orchestrator post-verdict.

---

## §4 Owner decision list

1. **Merge queue vs `strict=true` (the merge-result gate on main).** Options: (a) **merge queue** — M1+M2,
   ~7.5/8, P1's flagship recommendation and P3-OQ6 ("the only ruleset lever that BINDS the admin-batch
   class"); **Step 0 (prerequisite): wire `merge_group:` into ci.yml + codeql.yml and reconcile the PR-only
   `release-train-archive-guard` `if` (ci.yml:423)**, or the queue stalls all merges incl. the archive-PR
   exemption. (b) **`strict=true`** — M2 only, ~5/8, P1's fallback and P3-OQ5 one-setting flip; misses
   #801/#803/batch, O(N²) thrash. Recommendation: queue if available, else strict. **Unblocks:** UI
   availability check + a `merge_group` wiring smoke-test on a scratch queued PR. Source: **P1 §1/§7, P2
   §5(ii), P3 §4/OQ5/OQ6.**
       - A:

2. **ci.yml cancel-in-progress per-SHA fix (near-free, high value — flag as such).** Change the main-verify
   concurrency from `group: ci-${{github.ref}}, cancel-in-progress: true` (rapid serial merges cancel each
   other → only the last is verified) to per-SHA `group: main-verify-${{github.sha}}, cancel-in-progress:
   false` so every merge is verified. Recommendation: adopt — trivial, high value, ships with G3.
   **Unblocks:** nothing (a one-stanza change). Source: **P2 §3.**
       - A:

3. **Required-review (`pull_request`) rule adoption.** Options: adopt (`required_approving_review_count:1`,
   `dismiss_stale_reviews_on_push:true`) vs not. Limits: the owner cannot self-approve own PRs (falls back
   to admin bypass); it **breaks the release-train archive-PR hands-free auto-merge** (App-token author
   can't self-approve). Recommendation: P1 optional/last, only if the owner will read every fleet diff; do
   NOT remove owner bypass to give it teeth. **Unblocks:** owner commitment to review fleet diffs + accept
   the archive-PR auto-merge clash. Source: **P1 §2.**
       - A:

4. **Bypass-actor cleanup (defense-in-depth).** Remove Integration bypasses 1210556 (**cursor**), 1236702
   (**claude**), 1276151 (**identify first**), and review the **DeployKey** bypass; keep RepositoryRole 5
   (owner). Framing: defense-in-depth + hygiene, NOT a queue prerequisite; ~0 cost; after removal the
   archive PR must PASS (not bypass) the 13 checks. P3-OQ7: near-zero flood effect alone; confirm the
   1236702/1276151 peer expectations before touching. **Unblocks:** identify 1276151 (owner UI); confirm
   DeployKey-to-main usage; @claude scratch-PR smoke-test after removal. Source: **P1 §3, P3 §4/OQ7.**
       - A:

5. **Cursor dashboard asks (all verify-in-dashboard).** Request: concurrency cap (≤5), schedule cadence,
   per-class disjoint file scopes, per-run PR budget, draft-PR creation, target-branch selection; and
   confirm the automation count (3 vs 4). The only source-side throttle if Cursor supports it; none is
   assumed. **Unblocks:** the owner verifies each capability in the Cursor dashboard / GitHub App
   installation settings. Source: **P3 §2/OQ1-OQ2, P1 §6(i), P2 §5(i).**
       - A:

6. **Blocking-option stages.** Path: **advisory → strict/queue → draft-only/integration-branch → full
   mediation**, with P3's staged entry/exit criteria (Stage-0 exit: verdicts match reality across ≥2 batches
   AND no un-reported batch merged; Stage-3 terminal, revert by re-granting access). Recommendation: P3's
   Stage 0 + Stage 1 strict flip in parallel; escalate only if damage recurs (blocking costs Cursor's
   self-healing #800 + SPOF/concentration). **Unblocks:** Stage-0 calibration; OQ2 draft/target capability
   for Stage 2. Source: **P3 §4, P1 §6(v), P2 §5(v).**
       - A:

7. **Supervisor adoption (Stage-0 build list).** Build: `util/fleet_triage/predict_merge.py` +
   `.claude/agents/fleet-supervisor.md` + `tests/test_predict_merge.py` +
   `tests/test_fleet_supervisor_contract.py`, with both tests wired into the ci.yml enumerated battery AND
   AGENTS.md's run-all list, plus the AGENTS.md co-changes (agents node, `util/fleet_triage/` tree entry).
   Recommendation: P3's recommended start (read-only per OQ4). **Unblocks:** nothing external — an in-repo
   owner-merged PR. Source: **P3 §1.**
       - A:

8. **P2 gate build order.** Order: (1) **G3 + G1 module** (silent-deletion net, bypass-proof at G3);
   (2) **G4 pre-commit split** (cheap, kills the highest-blast-radius #3 class); (3) **G1 per-PR + G2 docs**
   (soak advisory, then promote in the ruleset — never via the QG `needs:`); (4) **G5 observability**.
   Recommendation: P2 §6 ranked order. **Unblocks:** land the untracked ad-hoc census scripts in-repo first
   (`util/sequence_safety/`); wire each lint-test into the battery + AGENTS.md in the same PR. Source:
   **P2 §6.**
       - A:

9. **Open-PR budget alarm.** Options: a scheduled Actions workflow (`gh pr list` count → Slack,
   non-blocking) — P1's recommendation, matching release-train.yml:325-366; the P2 G5(i) queue-meter CI-step
   variant; and the P3 supervisor batch-budget process variant. Recommendation: adopt P1's scheduled workflow
   as the near-free detector. **Unblocks:** `SLACK_WEBHOOK_URL` present (skip-if-unset). Source: **P1 §5,
   P2 §5(i), P3 §5(i).**
       - A:

---

## §5 Process-validation record (Task 4)

- **Pre-emission**: the program prompt itself passed the house triple before emission — prompt-validator (RUBRIC R1–R5, PASS, 2 minors fixed), adversarial fact-refuter (45 confirmed / 5 refuted → corrections applied), feasibility reviewer (PASS-conditional → all 7 SHOULD-FIXes applied) — per the prompt's provenance header (ml#844).
- **Execution grounding**: re-grounded at `3915d1e6` before any action (discovery bundle all-probes-ok; ruleset/bypass/apps live-probed; census universe re-derived and reconciled ±1 as required).
- **Census**: two independent census agents (C1 Python/AST, C2 docs-reconstruction) + a completeness critic (C3) with deterministic spot-checks; every finding carries a guilty-merge SHA and last-good blob ref; adjudication via the `-m`/`-S` unmasking technique; post-heal re-run (§2.6).
- **Proposals**: 3 authors blind to each other; 9 first-round validator verdicts; convergent independent findings treated as high-confidence (the P1 merge_group gap found by 2 reviewers; the P2 Quality-Gate wiring defect found by 3); revisions applied by dedicated revision agents with zero disputes; failed lenses re-validated to PASS in one cycle each (P2 required none — zero MUST-FIX across its triple).
- **Notable process events**: a transient API session limit interrupted three agents mid-flight (C1, R1, R3); all three were resumed from their transcripts with context intact and completed normally — no work lost, no re-derivation skipped. One Phase-0 figure (the monthly-storm precedent) failed live re-derivation and is corrected in §1's addendum rather than silently carried.
- **Final read-through**: Final read-through (RT): READY-WITH-FIXES — 7 internal-consistency/structure fixes applied; ≥45 references (ruleset 13805432, 13 guilty + 6 ancillary SHAs, PR states #852/#853/#845/#838/#842/#843/#743/#844, the #709 timestamp, the bimodal monthly counts, and heal-branch contents) spot-verified against the live repo/GitHub; all core findings confirmed TRUE.

---

## §6 Owner-side open probes (requested, not performed)

- Identify always-bypass integrations **1236702 = `claude` (confirmed via API)** — decide whether the Claude GitHub App should retain always-bypass — and **1276151 (unresolvable via public API**; read from Settings → GitHub Apps / the ruleset bypass list UI). Review the `DeployKey` bypass entry.
- Retrieve the Cursor dashboard automation configs behind the per-class UUIDs (test-coverage `4e249ce1-…` from #729; docs `294b2ed6-…` from #746; plus the bug-investigation class): schedule/cadence, concurrency, per-class prompts, file scopes. Reconcile the automation count (3 per Phase-0 vs 4 fleet check names incl. "Find vulnerabilities").

---

## Appendix — program artifacts

- Census tooling (committed with this PR under `util/ad-hoc/`, per the mandatory script-placement rule): `2026-07-28_flood_census_universe.py` (pinned universe), `2026-07-28_flood_census_symbol_screen.py` + `2026-07-28_flood_census_adjudicate.py` + `2026-07-28_flood_census_ci_yml_screen.py` (C1), `2026-07-28_docs_census_c2.py` + `2026-07-28_docs_census_v2_c2.py` + `2026-07-28_fp_transition_c2.py` (C2; C3/C4 ran adjudication via git plumbing, no scripts). Retire when: the guardrail decisions land
  and the census class is productionized (P2's `util/sequence_safety/`, P3's `util/fleet_triage/`).
- Heal PRs: **#852** (tests + ci.yml) and **#853** (docs), both owner-gated. Prior in-flood heals: #838, #842, #843.
- The full proposal texts were developed and validated in program scratchpad space; their decision surfaces (tables, ranked sets, staged paths) are carried verbatim in §3.
