# HANDOFF — Shared-session-memory arc: everything that remains after the fleet ratchet was promoted

**Date**: 2026-08-28
**Origin session**: `p5 ports, session split [3c9662]` (worktree `idempotent-dreaming-panda`)
**Predecessors**: [`HANDOFF_2026-08-26_p5-continuation-verification-and-validation.md`](HANDOFF_2026-08-26_p5-continuation-verification-and-validation.md)
(this lineage) and [`HANDOFF_2026-08-26_p5-promotion-preconditions-de-advisory-and-slack.md`](HANDOFF_2026-08-26_p5-promotion-preconditions-de-advisory-and-slack.md)
(the cut lineage, ml#1400). Every remaining item of both is done or carried below (*Validation*).

**Validation status**: two rounds by independent agents — see *Validation*. Provenance, scoped: PR
and issue states, squash SHAs, ceilings, `AGENTS.md` sizes, ruleset counts, soak figures and the
`MEMORY.md` size were re-run against GitHub or this checkout on 2026-08-28; the cut session's
facts are cited from ml#1450's prep note (commit `021590a9`), not from messages.

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** arc in `juniper-ml`. Plan of record:
[`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md)
(§4 phases, §5 owner decisions, §6 the soak, §7 residual risk); tracker **ml#1326** (the ledger —
read newest first with `gh issue view 1326 --repo pcalnon/juniper-ml --json comments --jq
'.comments[-3:]'`; every comment is authored by `pcalnon`, so a session is identified by the
worktree/branch it names); soak ledger
[`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md).

**Dup-guard first — durable identifiers, not session names.** (1) `gh pr view 1450 --repo
pcalnon/juniper-ml --json state,headRefName`: while OPEN the cut session (`p5 memory` lineage,
earlier `memory budget`) is live and owns item A; read the plan from its branch, not `main`. MERGED
is not "gone" — its canopy/cascor work starts after #1450 — so before claiming any of A also check
the newest #1326 comments and `gh pr list --state open --search AGENTS.md` on juniper-canopy and
juniper-cascor, and take A only if neither shows the cut lineage active. (2) Post a claim comment on
#1326 naming your worktree, branch and the items you take, BEFORE starting. (3) `ListAgents` /
`SendMessage` are best-effort — never wait on a reply. Two sessions duplicated each other from ONE
handoff on 08-25.

### Completed so far (the arc)

- **juniper-ml**: P0 `MEMORY.md` eviction, P1 canary, P2→P4 — `AGENTS.md` cut to 37,079 chars under a
  38,000 ceiling; `Memory Budget` BLOCKING and REQUIRED (2026-08-20).
- **P5 ratchet**: ports merged 08-25/26 in the eight target repos; `--advisory` removed + slack
  declared 08-26; **PROMOTED 2026-08-27** — with juniper-ml, **nine repos carry `Memory Budget` as a
  required check** (the plan's "8 of 9 governable" counts slacker, which has no `AGENTS.md`, and
  excludes juniper-ml). Ruleset ids, before → after counts and the snapshot path
  `~/.local/state/juniper-ruleset-snapshots/` are in the plan §P5 banner and on #1326.
- **Cuts (step e), 2026-08-28 CDT (`mergedAt` 2026-08-29T00:12–00:20Z), cut session**:
  cascor-client#142 (`e19d7926`, 34,695→15,832, ceiling 18,414), data#296 (`9f9c0b8c`,
  43,493→24,965, ceiling 26,965), data-client#176 (`e3a8ddb9`, 28,369→15,531, ceiling 17,604);
  recurrence#135 (`315d014b`) raised its ceiling 13,698→20,000 and **deferred** its cut (11,578
  chars; no `docs/` at all). Each primary already holds its trimmed file.
- Tooling fixed on the way: `measure-growth --ref` in `util/ad-hoc/2026-08-25_p5_port_memory_budget.py`
  (ml#1398); the census `util/ad-hoc/2026-08-26_p5_fleet_state.py` (ml#1403, `a0416ff2`);
  `find_ruleset` in `util/ad-hoc/2026-08-20_require_context_safely.py` (ml#1429); and, in ml#1450
  (open), the relocation tool `util/ad-hoc/2026-08-19_p3_relocate_section.py` — fence-blind
  `extract()`, `heading_level` mistaking `# text` shell comments for headings —
  with `tests/test_p3_relocate_section.py` wired into ci.yml.
- All 12 centralized arc worktrees removed and every sibling primary fast-forwarded (per the cut
  session; `ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep memory-budget` → none).
  Harness-created `.claude/worktrees/` dirs of merged arc sessions remain (e.g.
  `fluttering-bubbling-newell`, ml#1380's branch) — liveness-probe before touching any.
- Soak (§6): **INCONCLUSIVE** — 35/35 seeded runs, 24 follows / 11 misses (68.6%, 95% CI
  [0.520, 0.814], boundary 0.75); 5 of the 11 are open rung-2 hazard escalations.

### Remaining work

**A. Held by the cut session — point at ml#1450, do not redo.** ml#1450 (OPEN, branch
`docs/p5-cut-canopy-cascor-prep`; its files exist only there until it merges — read one with
`gh api -H 'Accept: application/vnd.github.raw' 'repos/pcalnon/juniper-ml/contents/<path>?ref=docs/p5-cut-canopy-cascor-prep'`)
carries: the prep note `notes/JUNIPER_2026-08-28_JUNIPER-ECOSYSTEM_P5-CUT-CANOPY-CASCOR-PREP.md`;
the cut driver `util/ad-hoc/2026-08-28_p5_cut.py` (`status` read-only, plus
`prepare|ship|waive|bump-date|raise-ceiling`); `2026-08-28_hazard_triage.py` +
`2026-08-28_resident_gap_scan.py` (the first two finder versions were vacuous — it needed a positive
control); the section inventory, two overlap probes and the gated `2026-08-28_p5_worktree_cleanup.py`;
the relocation-tool fix; **and the plan §P5 banner rewrite** (*CUT IN PROGRESS — 3 cut, ~50,200
resident chars removed; recurrence a policy ceiling raise; canopy and cascor blocked; cascor-worker
and deploy cuttable, unclaimed*). Do NOT edit the plan file on another branch while #1450 is open —
a whole-file publish would revert one of the two; if its banner is incomplete, review-comment on
#1450. What that lineage still holds:
- **The canopy cut.** Prerequisites, all in the note: (i) destination (§7 item 1, resolved) — a
  split: ~27,700 chars of documentation-about-documentation → `docs/DOCUMENTATION_OVERVIEW.md`, the
  rest → a new `docs/AGENTS_REFERENCE.md`; `docs/REFERENCE.md` stays the index it is, with one row
  per destination; canopy's `conf/memory_budget.json` `_README` line calling REFERENCE.md "the
  migration DESTINATION" (inherited from ml's template) gets corrected; (ii) **hazards triage before
  the cut** (§6a) — canopy has no `## Hazards`, and a size-driven cut cannot tell a lookup-reference
  from a must-not-look-up warning; the agreed resident set is five ranked bullets, the first NEW TEXT
  to draft (the CRITICAL Dash `no_update` directive at `dashboard_manager.py:3869`, absent from
  `AGENTS.md`); (iii) the primaries — canopy's and cascor's both run live services owned by the
  `canopy e2e` session, which signals the cut session when they are free; an inheritor checks with
  `git -C /home/pcalnon/Development/python/Juniper/juniper-canopy status --short --branch` (and
  `…/juniper-cascor`) plus `util/ad-hoc/2026-08-20_worktree_liveness_probe.py`. A cut merged before
  its primary can be pulled loads BOTH copies in every new worktree — worse than not cutting (plan
  §P5 HAZARD).
- **The cascor cut.** Two decisions still open (note §7 items 2–3): a new `docs/REFERENCE.md` versus
  the existing `docs/INDEX.md` as destination, and tier A or A+B scope. Unaffected by the tool
  defect (§6c: all nine sections extract fully). Never cut from a checkout that predates #1450's fix.
- Cut order is `headroom ÷ rate` (rate alone was the *port*'s input), but a days figure for cascor
  is a window artifact and the note's §8 retracts the earlier "~47": 30-day rate 711 chars/day
  (≈13 days), 14-day rate 142 (≈68). The structural fact: **cascor's headroom is 9,609 chars, and
  the 30-day window's largest single commit is also 9,609** (14-day: 1,982) — the slack rule sized
  the ceiling from that commit, so one commit of a size cascor has already produced exhausts all of
  it. canopy: 2,000 headroom at ~66/day. Re-measure with `measure-growth --ref origin/main` before
  scheduling.

**B. Genuinely unclaimed — the two repos in the 30-day bucket.** cascor-worker (35,126 chars,
ceiling 37,126) and deploy (34,569 / 36,569): uncut, ~2,000 chars of headroom each at ~66 chars/day,
nobody holds them; the driver in ml#1450 works on them as-is once it merges. Whether they get a cut
at all is owner decision C.3; if yes, one PR each, hazards triage first, the same G3 local run.
Tracker #1326's title still says *cut not started* — retitle it after #1450 merges (`gh issue view
1326 --json title` first; no PR carries that change).

**C. Owner decisions pending — present them once, do not decide them:**
1. **The soak's next step (the ladder is fixed in advance, plan §6 — do not re-open it).** The
   ledger prescribes rung 1: index rows for the four facts never retrieved from prose, then re-soak
   — and its own conclusion narrows that to index rows for the **policy** facts only, since three of
   the four (P19, P14, P23) are already discoverable at their point of use. In tension with that
   conclusion: the policy stratum already follows 24/24
   (`HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md`, corrected in ml#1376), so a
   policy-only experiment cannot move its rate — flag the tension to the owner rather than
   resolving it here. The five open rung-2 escalations are, per the ledger, **source-recovered
   correct answers scored conservatively**: the ladder says a CI gate or hook each (discharged only
   after one lands, `soak_ledger.py resolve --obs-id <id> --ref <PR>`); the ledger says whether to
   re-score source-recovery as its own outcome is an owner decision, not a scorer's. INCONCLUSIVE may
   not be reported as a pass or a failure.
2. **`MEMORY.md` eviction — DEFERRED by the owner 2026-08-27** (#1326 comment, 2026-08-28 20:22 CDT),
   whose recorded trigger is verbatim: *"do not re-propose until the index nears the 24.4 KB read
   limit"*. The index was 20,635 bytes / 125 lines at 2026-08-28 20:00 CDT (the owner's figure;
   re-measure with the `wc -c -l` line below), growing ~0.8 KB/day, against a harness cap of 25,000
   bytes / 200 lines whose truncation is silent and drops the NEWEST rows (mechanism fact base §2 /
   §8b, cited at `notes/JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md:1157`).
   This session's *proposal*, not the owner's decision: read "nears" as ≥ 22,000 bytes (≈3 KB of
   margin) and have the remedy ready — finished-work eviction via
   `util/ad-hoc/2026-08-19_memory_index_evict.py` (SHA-guarded, dry-run by default).
3. **Cut or not, for the repos with no cut decision**: cascor-worker and deploy (item B) and
   recurrence (deferred; 8,422 chars of headroom under a 20,000 ceiling). The plan's §5 #2 target
   (32,443) was for juniper-ml only and is itself unmet at 37,079; the fleet has no target.
4. **juniper-ml's own headroom is 921 chars; the last fleet-wide fan-out was +1,982**, and four other
   repos (cascor-worker, deploy, data, data-client) sit at ≤ 2,073. Before the next fan-out lands, the
   owner picks one: (a) relocate ~1,100+ chars first (G3 run), or (b) raise `ceiling_chars` in
   `conf/memory_budget.json` in the SAME commit that carries `Allow-Ceiling-Raise: AGENTS.md - <reason>`
   — a commit body on the PR branch (CI reads `git log FETCH_HEAD..HEAD`; the trailer without the
   edit does nothing) and carried into the squash message, the only place it survives on `main`.
   Not `Allow-Budget-Overrun`: that is a loan with no ledger that blocks the next author.
5. **Parent `Juniper/AGENTS.md`** (§5 #8, §7 #4: ungoverned, unversioned, additive to all nine) and
   **the worktree settings asymmetry** (§5 #9) — both "Yes, separately" in the plan, and neither has
   a recorded owner decision: the 08-25/26 handoffs bundled them with the LEAVE IT below, but the
   recorded 2026-08-20 decision names only worktree *convergence* (P0b). Confirm with the owner
   rather than assume; do not call either plan row stale.
6. **Handoff length**: the procedure says ~500 words; the archive median is 1,190 (n = 144); this
   prompt is ~2,200 words (~2,850 with the wrapper). Options: amend the figure, add a gate, or compress.

Closed — do not re-propose: worktree convergence, P0b (owner: LEAVE IT, 2026-08-20;
`HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md:206`); Skills (§5 #7, deferred until a
real pointer-follow problem); the `MEMORY.md` 120-byte cap on new entries (§5 #4).

**D. Small engineering items, unowned:** `util/ad-hoc/2026-08-20_require_context_safely.py`'s
`TARGETS` (7 targets + juniper-ml) omits `juniper-recurrence` — it is the default READ and WRITE roster
for any no-`--repo` run; recurrence is already required, so adding it makes `--apply` a verified no-op
there and lets `--status` report all nine (the census has its own roster and already lists
recurrence); the waiver *loan* (§5 #6, §7 #7) has no central ledger — `Allow-Budget-Overrun`
suppresses the failure and moves nothing, so a loan is visible only in the trailer; the cursor drafts
stuck at *expected* on pre-port heads (canopy #513 #512; cascor #584 #583; data-client #168 #167;
cascor-client #134 #133 #132 #131 #130) need nothing now — when one is readied, `update-branch`
re-runs CI (`ready_for_review` is not a trigger in any of the eight); G3 takes a single `--dest`, so
canopy's two-destination split needs a repeatable `--dest` or one run per destination.

### Key context

- `Memory Budget` is `skipped` on every `main` commit by design (`if: pull_request || merge_group`);
  recurrence's standalone workflow publishes nothing on `main`. The pre-flight's "observed" is
  PR-head check-run names. `--ratchet` only LOWERS existing ceilings, to the exact current size
  (zero headroom — what the fleet `_README`s call "seeding"); it never raises and never creates an
  entry, so after a cut hand-edit the ceiling with slack.
- G3 (`util/relocation_check.py`) lives in juniper-ml and is absent from canopy and cascor (404;
  check the others before assuming); for a fleet cut the **local** run from ml's checkout is the
  only content-loss control — a green target PR proves nothing (plan step e):
  `python3 util/relocation_check.py --repo-root <target worktree> --base origin/main --head HEAD
  --source AGENTS.md --dest docs/REFERENCE.md --expect-removals` — one `--dest` per run, so for
  canopy run it once per destination and require every removed line to pass in at least one run;
  exit 0 complete / 1 content lost / 2 misuse or broken machinery, never a pass. **G3 is blind to
  what failed to move**: it checks that every removed line is in the destination, so a truncated
  extraction leaves the remainder orphaned under a "Moved to …" pointer with G3 passing — the unfixed
  tool would have truncated 8 of canopy's 11 candidate sections that way (`## Quick Start Commands`,
  10,009 chars, to 62; note §6c, with the table). A completeness check that verifies what moved cannot
  see what failed to move — pair G3 with the section inventory and read the pointer-only sections.
- A raw `grep -c -- --advisory` counts comments; the census is trustworthy only from ml#1403 on.
  Read invocation lines and files, not flags.
- Merge path on this strict, fast-moving `main` (the auto-memory rows cover the mechanics; this is
  the ORDER): one signed commit → `gh pr create` → `util/wait_for_checks.py --pr N` → **present the
  PR; only on the owner's explicit approval of it** → `gh pr merge --squash --auto --subject …
  --body-file …` → confirm with `gh pr view N --json state,autoMergeRequest --jq '"\(.state)
  armed=\(.autoMergeRequest != null)"'` → `OPEN armed=true`. Arming `--auto` IS the merge decision —
  never arm before approval. Auto-merge does not update a BEHIND branch: `gh api
  repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT` each time `main` moves, then re-wait.
- Two recording traps from 08-28: `util/safe_merge.py`'s `MERGED #N at <sha>` names the HEAD it
  merged, not the squash commit — record `gh pr view N --json mergeCommit` (`.mergeCommit.oid`); the
  two coincide only when the PR never re-synced. And backticks inside a double-quoted shell argument
  are command substitution — `gh … --body "…"` and `git commit -m` silently delete the identifier
  and exit 0; use `--body-file` / `-F`.
- From a worktree-isolated session, `git -C <this repo's primary>` is refused; `git -C <sibling
  repo>` runs, one plain command per call (compound lines, loops and heredocs are refused —
  multi-step logic goes in a `util/ad-hoc/` script). The primary pull is an owner action.

## Verification commands

```bash
git fetch origin
gh pr view 1450 --repo pcalnon/juniper-ml --json state,mergedAt --jq '"\(.state) \(.mergedAt)"'   # OPEN null until it merges; its note + tools are branch-only until then
git show origin/main:notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md | grep -n "^\*\*Status:" | head -1   # "has not started" until ml#1450 merges, then "CUT IN PROGRESS"
gh issue view 1326 --repo pcalnon/juniper-ml --json title --jq .title                                                # "cut not started" until retitled (item B)
gh pr view 142 --repo pcalnon/juniper-cascor-client --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'   # MERGED e19d7926; data#296 9f9c0b8c; data-client#176 e3a8ddb9; recurrence#135 315d014b
gh api repos/pcalnon/juniper-recurrence/rules/branches/main --jq '[.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[]|select(.context=="Memory Budget")]|length'   # 1 — same on canopy, cascor, data, data-client, cascor-client, cascor-worker, deploy, juniper-ml
python3 util/soak_ledger.py report | grep -E "verdict|rate|hazard"        # INCONCLUSIVE, 68.6%, 5 open misses
python3 util/memory_budget_check.py                                        # OK 37,079 / 38,000
wc -c -l /home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md   # vs 25,000 bytes / 200 lines
```

## Git status at handoff

- Worktree `.claude/worktrees/idempotent-dreaming-panda`, branch `docs/handoff-2026-08-28-arc-remaining-work`
  rebased onto `origin/main` before its archive PR; nothing staged; this file is the only change and
  is committed by that PR. Every earlier branch of this session is merged and deleted (ml#1395,
  #1398, #1407, #1428, #1429).

## Validation

**Amputation check** (SOP, ml#1285): the eight remaining-work items of the cut lineage's predecessor
(ml#1400 handoff) are done (canopy#529, post-merge census, ledger + peer, archive PR, promotion,
worktree cleanup) or carried here (step e → A; owner decisions → C); the five of this lineage's
predecessor likewise (banner, promotion → done; peer artifacts → A; MEMORY.md → C.2; decisions → C).

**Round 1** — four independent refuting agents, one lens each, budget-capped (eight uncapped ones
died on the shared API quota on 08-26; four capped ones reported in full): grounding 0 critical /
5 major / 6 minor; completeness-executability 1 / 5 / 8; adversarial-consequence 2 / 5 / 8;
procedure-conformance 0 / 5 / 9. Root cause of most majors: ml#1450 moved after the draft's
snapshot of it (the banner rewrite, the relocation-tool fix, the hazards prerequisite, the
retracted "~47"). The two criticals: item B originally told the reader to write the banner that
#1450 already rewrites; the merge-path bullet armed auto-merge before the approval step. All applied.

**Round 2** — three fresh agents on the corrected text (SOP: the fix pass introduces its own errors):
the repo's `prompt-validator` custom agent (rubric R1–R5; anchor re-probe) returned **FAIL, 1 major /
6 minor** — the major was introduced by round 1's fix: a "re-raise at 22,000 bytes" trigger this
session invented, stated under owner decisions against the owner's recorded "nears the 24.4 KB read
limit" — now quoted verbatim and the figure re-labelled a proposal; an adversarial fact-checker
0 / 3 / 10 (the "Closed" line conflated worktree convergence with the settings asymmetry — split;
G3 exit codes; window-dependence of cascor's max commit; UTC merge stamps); a fresh-session
procedure audit 0 / 4 / 12 (the dup-guard said the cut session owned item B; G3's single `--dest`
versus canopy's split; MERGED ≠ gone; length disclosure). All applied; the four chat-sourced cut
figures the validators could not check were landed by the cut session in the #1450 note
(`021590a9`) and are now cited from it.
