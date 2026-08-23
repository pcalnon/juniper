# HANDOFF — Memory budget, the pointer-follow soak, and its side-findings

**Date**: 2026-08-23
**Origin session**: shared-session-memory / soak arc (juniper-ml)
**Validated by**: three independent agents (grounding / completeness / adversarial)
before archiving. They found **4 CRITICAL + ~30 lesser defects** in the first draft,
including an amputated rollout procedure, a merge command that understated a persistent
server-side effect, and a recommended experiment that was arithmetically null. All folded
in; every figure below is post-correction.

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** arc in `juniper-ml`. Plan:
[`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md);
protocol + terminal soak result:
[`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md)
(§7 how to run a probe, §12 pilot + side-findings, §13 batch 2, §14 terminal result).

**The soak is COMPLETE and the budget is hardened.** What remains is a prioritised
backlog, not an interrupted task.

### Completed (8 PRs, all merged)

- **#1206 / #1226 / #1250 / #1260** — the pointer-follow soak, end to end.
  Terminal: **35/35 runs, 15/15 probes, 24 follows / 11 misses, 68.6%,
  CI [0.520, 0.814] → INCONCLUSIVE** (the interval spans the 0.75 boundary).
- **#1246** — worktree cleaner gates on git's `locked` flag; `--force` dropped.
- **#1271** — anti-loosening ceiling guard (raising `ceiling_chars` FAILS) + relocated
  `### CI/CD Workflows` (−7,865: 44,657 → 36,792).
- **#1274** — ceiling lowered by **hand-edit** 45,084 → **38,000** (36,792 + 1,208
  deliberate slack). **Not** `--ratchet` — see the hazard below.
- **#1277** — a failed `--systemd` plant no longer deletes a nohup stack's pidfile.

### Remaining work, highest value first

1. **Seven verified side-findings.** The ledger records them as prose in **§12**
   (`### Live defects the probes found as a side effect`) with **no** file:line
   references — the anchors below were derived in this session against `878029e` and
   are the only ones that exist. Line numbers drift; re-verify before acting.
   - **`main-verify`'s G3.1 catch-up base ratchets on GREEN, not SCREENED**
     (`.github/workflows/main-verify.yml:135`, `status=success`). One finding freezes
     the base, so every later merge re-screens the same window — each red guarantees
     the next and innocent commits are failed for someone else's damage. This is the
     mechanism behind the recurring main-verify reds.
   - **Both `pip-audit` jobs audit nothing** — `pyproject.toml:26` is
     `dependencies = []`, so both scan pip-audit's own tree and report green.
   - **The `JUNIPER_ROOT` fan-out skips a canonical repo silently when its `claude.yml`
     is absent** (`util/validate_claude_yaml_access.bash:97-102` — `if [ -f "$f" ]`, no
     else; the only warning, at `:104`, fires when *zero* repos match). `juniper-recurrence`
     has none, so the weekly audit covers 8 of 9 and exits 0.
     **`DEFAULT_REPOS` already includes recurrence** and is pinned by
     `tests/test_validate_claude_yaml_access.py:285` and `:325` — **do not touch those
     two tests; they are correct guards.** The fix is a per-repo warning on
     present-but-file-missing, **NOT** adding a `claude.yml` to juniper-recurrence,
     which would give a public repo a new `ANTHROPIC_API_KEY`-spending workflow.
   - **`juniper-doc-tools/juniper_doc_tools/_ecosystem.py` is an ungated third repo
     list** missing `juniper-recurrence` (verified: 0 occurrences).
   - **12 tags exist with no Release** as of 2026-08-23
     (`comm -23 <(git ls-remote --tags) <(gh release list)`) — **this count moves with
     every release cut; re-measure.** The `Require a GitHub Release` step is unreachable
     dead code in all six publishers (`if: github.event_name == 'push'` while `push` is
     not in `on:`).
   - **`.github/workflows/publish.yml:126` is an unconditional `sleep 30`** — 77% of a
     measured 39s step; all pip work is ~9s.
   - **The stacked-PR date remedy at `docs/REFERENCE.md:1849` is backwards on
     durability** (probe P09). It says re-bump the *base*, which has a one-day shelf
     life; having the *child* bump the line is stable. Relocated out of `AGENTS.md` by
     #1271 — still wrong, now at a new address, and still in the loaded reference.
2. **Two vacuous/contradictory gates found in passing.**
   - `tests/test_juniper_plant_all.py:929` `test_ss_missing_fail_open` sets
     `PATH = <stub>:/usr/bin:/bin` but `ss` lives at `/usr/bin/ss`, so it never
     simulates absence. It passes identically whether the helper fails open or closed.
   - `util/memory_budget_check.py:69` / `:75` accept **only** the bare `<path>` trailer,
     while
     [`notes/JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-ARCHITECTURE-SYNTHESIS-2.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-ARCHITECTURE-SYNTHESIS-2.md)`:538`
     mandates a `<path> — <reason>` form and even claims the checker fails a bare one —
     the exact inverse. An author following the design docs writes a trailer that is
     silently ignored and stays red.
3. **The soak's next step is NOT the obvious rung 1.** The verdict routes to rung 1 (add
   index rows, re-soak), but **the obvious version of that is a null experiment**:
   measured from the ledger, the **policy stratum is 22 runs / 22 follows = 100%** and
   the source-recoverable stratum is 13 / 2 = 15%. Adding index rows to the policy facts
   cannot move a rate already at 100%, and §14 argues an index row buys little for the
   source-recovered four. **Resolve this before spending another 35-run cycle**: either
   (a) register NEW policy probes with headroom to move, or (b) accept the measurable
   question is settled and take the owner decision on re-scoring source-recovery instead.
   Operating procedure is ledger **§7**, not §14 — hand the probe's `task` to a fresh
   session and **never mention the soak, the fact, or the pointer**; priming is what
   invalidated an entire arm. `severity`/`area` come from the frozen registry and cannot
   be passed at the CLI. If a pointer no longer resolves, fix it and **do not score the
   run**. **Never re-inline** — fixed in advance, non-negotiable.
4. **P5 fleet rollout — NOT started, no tracking issue in any repo.**
   **THE PROCEDURE IS NOT IN THE PLAN.** Plan §P5 is a five-line stub carrying *stale*
   sizes (94,373 / 70,118). The full recipe survives only here; fold it into the plan on
   the first P5 PR. Order is mandatory: **rate axis before level axis** — a ceiling set
   *after* a cut locks in the inflated level, and a level fix without a rate fix is undone
   in ~44 days. That is how `AGENTS.md` reached 170K **while under four active CI gates**
   (172 of 200 merges grew it; 14 shrank it, by 2,628 bytes total). **Do not take
   "canopy is 93K, big win first."**
   - **a.** Copy `util/memory_budget_check.py`, `tests/test_memory_budget_check.py`,
     `conf/memory_budget.json`. Both scripts take `--repo-root` and are repo-agnostic.
   - **b.** **Seed that repo's ceiling by running `--ratchet` IN the target repo — never
     by transcribing a number from a note.** Do not copy 38,000 or 32,443 from here.
   - **c.** Copy the standalone `memory-budget` job from `ci.yml`. **Standalone — NOT in
     the Quality Gate `needs:`** (plan correction C9).
   - **d.** Soak `--advisory`, remove it, then run **three negative controls** before
     promoting: clean → exit 0, +500 chars → exit 1, waiver trailer → exit 0.
     **A blocking gate that cannot fail is worse than none.** Then promote:
     `python3 util/ad-hoc/2026-08-20_add_required_context.py --repo pcalnon/<repo>
     --ruleset-id <ID> --context 'Memory Budget' --apply` (dry-run by default; find
     `<ID>` via `gh api repos/pcalnon/<repo>/rulesets`).
   - **e.** Then G3, then the cut. **`juniper-cascor` has no `docs/REFERENCE.md`** —
     create the destination first.
   - **HAZARD, do not demote to a pointer:** the cut must land on that repo's `main`
     **with its primary checkout pulled** before any worktree carries the trimmed file.
     A trimmed worktree over an untrimmed ancestor is the **worst** case — loaded context
     goes **UP**, not down.
   - Measured sizes: canopy **93,151**, cascor **68,224**. Re-measure; do not transcribe.
5. **`MEMORY.md` forward-only cap (owner decision #4) never shipped.** Decided design is
   **120 bytes on NEW entries only; existing rows are not rewritten** (correction C7).
   Eviction shipped and bought only **+9 days**; rows cluster at 173–215 chars against a
   146.7 mean, so compression cannot close the gap — it needs **recurring** curation via
   `util/ad-hoc/2026-08-19_memory_index_evict.py`. The hard cap is **200 lines /
   25,000 bytes** and it truncates **silently, newest-first**. The file is itself
   **always-loaded**, so it competes with `AGENTS.md` for the same budget.
   **The blocker is enforcement surface** — it lives at `~/.claude/projects/…/memory/`,
   outside every repo, so no CI job can reach it. Pick a `util/` linter, a local hook, or
   documented discipline before writing code. Hard rule: **detail may be demoted;
   STATUS may not.**
6. **Parent `Juniper/AGENTS.md`** — deferred by the owner 2026-08-20. Additive to every
   session in all 9 repos, in a directory that is not a git repo.
7. **Worktree settings asymmetry (owner decision #9, "yes, separately") — untouched.**
   The primary checkout's `.claude/settings.local.json` is gitignored, so worktree
   sessions run without settings main-checkout sessions get. Plan §7.5: any `.claude/`
   destination is **outside the docs content-loss screen entirely**.

### Key context — read before acting

- **`AGENTS.md` is 36,960 / 38,000, headroom ~1,040 — RE-MEASURE, never trust this
  number.** It moved three times during the session that wrote this. Target 32,443
  (4,517 away). `python3 util/memory_budget_check.py` is authoritative.
- **The ceiling may now only move DOWN.** Raising `ceiling_chars` FAILS unless declared
  with `Allow-Ceiling-Raise: <path>` — deliberately a *different* trailer from
  `Allow-Budget-Overrun:`, because an overrun borrows against a standing ceiling while a
  raise moves it and erases everyone's debt.
- **`--ratchet` SEEDS; it never TIGHTENS after a cut.** In a repo with no ceiling yet
  (every P5 target) it is the *only* correct way to set one. After a real cut in a repo
  that already has one, it leaves ZERO headroom and fails the next author on one
  character — hand-edit with slack sized to the burn (+937 over four days / five PRs,
  median +58, one docs PR +605).
- **The rate axis reasserts itself in days.** After P3 the file ate 1,364 chars of slack
  down to 427 in four days.
- **Relocate by script** — `util/ad-hoc/2026-08-19_p3_relocate_section.py` — byte-for-byte,
  so G3 passes by construction. It rewrites relative links and **the order of its
  arguments is load-bearing** (rationale at `:54-73`); out of order it silently redirects
  every destination anchor back at the source, with no error.
- **`@path` imports save ZERO tokens** — eagerly inlined at launch. Any design resting on
  them is void; this is why the plan cuts and relocates rather than splits.
- **Plan §7 lists seven residual risks. Re-read it.** Three bear directly on the work
  above: **§7.2 — G3 is the only content-loss control, it runs `--advisory` in CI and
  does not exist post-merge, so a green PR proves nothing; the local `--expect-removals`
  run IS the control**; §7.6 — a path-scoped rule is lost at compaction, capping the
  ladder at rung 2 in practice; §7.7 — the overrun waiver is a loan with **no central
  ledger**, and the worktree count is now 32 (re-measure; never trust a count).
- **Plan §8's two "both live" items are CLOSED**, both by #1175:
  `tests/test_assert_release_tag.py` is wired in `ci.yml`, and the `--ref-type` doc drift
  is gone from `AGENTS.md`. §8 was never updated — do not re-investigate them.
- **Five hazard escalations are OPEN and must not be discharged.** All five are
  source-recovered *correct* answers — an artifact of the conservative scoring in §12.
  **`soak_ledger.py status` exits 1 because of them, by design, and its own output
  suggests `soak_ledger.py resolve` — do NOT run that.** The discharge is irreversible in
  an append-only ledger. Whether to re-score source-recovery as its own outcome is an
  **owner decision**. Note the instrument prints **rung 2 before rung 1**: rung 2 is
  neither taken nor closed, and rung 1 must not be allowed to imply it was settled.
- **The soak's real finding is not the rate.** All 35 answers were correct **as
  re-adjudicated in §14** (§12 still records P15 as wrong; §14 explains its discriminator
  was stricter than the source rule and was deliberately not re-scored). The split is
  *where the fact came from*: a fact with a nearby test or owning script is recovered from
  source; a pure-policy fact is retrieved from the prose.
- **A probe can be invalid three ways**, each found only by running probes: the fact never
  left the source; the discriminator is satisfiable without engaging the fact (P17); the
  discriminator is stricter than the source rule (P15).
- **The probe registry leaks, and containment is unreliable.** Identifier-shaped facts get
  grepped and surface `conf/soak_probes.json` — 8 runs discarded; prose-shaped facts never
  tripped it. **Rule for authoring the next round: store identifier-shaped facts in a form
  the subject's own grep cannot hit.** Holding files aside failed when a probe agent ran
  `git checkout`. Detection (`util/ad-hoc/2026-08-21_soak_probe_evidence.py`) is the
  load-bearing control.
- **Score retrieval from tool logs, never prose.** An agent citing a file it never opened
  is a miss. The scorer reads tool *results* as well as inputs — a directory-wide grep
  retrieves content without the path appearing in the command.
- **Merges here can silently revert.** #1271 conflicted with #1269, which had edited the
  very section being relocated; resolving to "ours" would have deleted that correction.
  Check `git diff origin/main...HEAD -- <file>` (three dots = against the merge base),
  never `git show HEAD` — #1183 reverted P3.2 through a merge commit while its tip showed
  +2 bytes.
- **Nothing is truncated except `MEMORY.md`.** The per-file "character limit" is a
  *warning*; the real hard limit is 4 MiB and it **skips the file whole**. 38,000 is a
  policy choice, not a system wall.
- **Set the `AGENTS.md` `**Last Updated**:` header to today's UTC date** — the check bites
  any PR authored after ~19:00 CDT.
- **Worktree convergence: owner said LEAVE IT** (2026-08-20). **Proposal A's Skills stay
  deferred** (owner decision #7) — revisited only on a *real* pointer-follow problem;
  INCONCLUSIVE is not that signal. Do not re-propose either.
- **Never pipe an exit-code-significant command through `tail`/`head`** — you get the
  pager's status. I did it; so did one validator. Use `set -o pipefail` or run unpiped.

---

## Verification commands

> **Ordering — read first.** All three ref-diff screens diff `origin/main..HEAD`. Run them
> **after committing**: on an uncommitted tree the range is empty and **all three report
> clean** — a vacuous pass, not a green light. `git fetch origin` first or `origin/main` is
> stale.

```bash
# The primary checkout is SHARED with other live sessions. Inspect before touching it.
git -C /home/pcalnon/Development/python/Juniper/juniper-ml status --short --branch
# Only if clean AND already on main:
git -C /home/pcalnon/Development/python/Juniper/juniper-ml fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-ml pull --ff-only origin main
# If dirty or on another branch: LEAVE IT (AGENTS.md Phase 7, F-6 guard).
# Verified 2026-08-23: clean, on main, at 878029e. RE-CHECK — do not assume.
# A worktree-isolated session cannot `cd <shared> && git ...`; the harness refuses it.
# Run everything below from YOUR worktree.

python3 util/memory_budget_check.py     # expect OK; RE-MEASURE headroom
python3 util/soak_ledger.py report      # expect INCONCLUSIVE, 35/35 runs, 15/15 probes,
                                        # "hazard 16 runs, 5 open misses"
python3 util/soak_ledger.py status      # EXITS 1 BY DESIGN (open escalations) — NOT a
                                        # failure. Do NOT run `resolve` to clear it.
python3 util/soak_ledger.py verify-probes                    # expect OK: 15 probes
gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
  --jq '[.rules[]|select(.type=="required_status_checks")
        |.parameters.required_status_checks[].context]|length'   # Memory Budget still required
python3 -m unittest tests/test_memory_budget_check.py tests/test_soak_ledger.py \
    tests/test_juniper_plant_all.py tests/test_cleanup_session_worktrees.py
# expect Ran 199 tests (34+74+62+29). KNOWN FLAKE: test_sigterm_ignore_escalates_to_sigkill
# (test_juniper_plant_all.py:1066) races /proc reaping after SIGKILL — 1 failure in 2 runs
# observed 2026-08-23. Re-run before investigating; not a main regression.
```

## Full local pre-flight (run all of it before every push)

```bash
pre-commit run --files <every changed path>
git fetch origin
juniper-symbol-loss-check   --base origin/main --head HEAD \
    --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'
# EXACTLY these three scopes — byte-identical to ci.yml and main-verify.yml. Do NOT add a
# fourth; a wider local scope fails where CI never would, and the fix people reach for is
# the allow-symbol-loss label.
juniper-docs-additions-check --base origin/main --head HEAD
python3 util/relocation_check.py --base origin/main --head HEAD \
    --source AGENTS.md --dest docs/REFERENCE.md --expect-removals   # RELOCATION PRs ONLY
                                        # exits 2 on a PR that removes nothing
juniper-check-doc-links --exclude templates --exclude history --exclude legacy \
    --exclude pull_requests --exclude releases --exclude analysis --exclude fixes \
    --exclude development --exclude CHANGELOG.md --cross-repo skip
python3 util/memory_budget_check.py
# If your commit carries Allow-Budget-Overrun / Allow-Ceiling-Raise, the BARE form cannot
# see it (memory_budget_check.py:233 — no git-log fallback) and will FAIL where CI passes:
#   git log --format=%B origin/main..HEAD > /tmp/mb-trailers.txt
#   python3 util/memory_budget_check.py --base-ref origin/main --trailers-file /tmp/mb-trailers.txt
```

## Merging

Merges happen only on **Paul's explicit per-PR approval**. Never merge to clear a queue.

```bash
python3 util/safe_merge.py --pr <N> --merge-method squash          # DRY RUN — read the verdict
python3 util/safe_merge.py --pr <N> --merge-method squash --execute --no-auto-fallback
```

The dry run is **not silent** — it prints `*** DRY RUN ***` and names the path it would
take. `--execute` **without** `--no-auto-fallback` arms a **server-side auto-merge net that
outlives this process** and is not pinned to the SHA this run vouched for
(`util/safe_merge.py:62-87`). If a run is killed after arming, the net is still live: check
`gh pr view <N> --json autoMergeRequest` before assuming nothing happened, and
`gh pr merge --disable-auto <N>` to take it down.

## Git status at handoff

- Branch `docs/handoff-remaining-work` in worktree `giggly-marinating-backus`,
  **0 commits ahead of `origin/main`**, never pushed.
- **This handoff file is UNTRACKED.** FIRST ACTION: commit it and open the archive PR —
  it exists nowhere else, and its `../../notes/…` links only resolve inside this worktree.
- `origin/main` at `878029e` (#1280 — a *different* arc: perf lane / logging).
- PR #1281 was open at time of writing. `gh pr list` before opening anything.

---

## Provenance

Origin session ran the soak from instrument v0.1 through a withdrawn design, a rebuilt
seeded arm, three probe rounds and four follow-on fixes. Reconstructible from the artifact:
`reports/soak/pointer_follow_soak.jsonl` holds **41 observation rows + 6 invalidate rows**
→ **35 valid** (8 further runs discarded as contaminated before recording); the registry
holds **15 probes + 10 retired**.

Three independent validators reviewed this handoff before archiving and found 4 CRITICAL
defects in the first draft — most importantly that it had **amputated the entire P5
per-repo procedure**, which exists nowhere else. Handoffs lose items across generations;
this is the third in the arc and it lost things its predecessor carried. **Validate the
next one the same way.**
