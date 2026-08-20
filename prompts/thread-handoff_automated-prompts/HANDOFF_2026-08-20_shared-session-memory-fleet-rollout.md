# HANDOFF — Shared Session Memory: fleet rollout and residual work

**Date**: 2026-08-20
**Origin session**: shared session memory (juniper-ml)
**Validated by**: three independent auditors (grounding / completeness / adversarial)
before archiving. Their findings are folded in; figures below are post-correction.

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** effort in `juniper-ml`. Plan:
[`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md);
its §4a/§4b execution logs are authoritative for what shipped.

**Plan phases P0–P4 and P0b are complete. P5 (fleet rollout) has not started**, and
the owner-set level target was not reached. Six items remain.

### Completed (15 PRs, all merged)

- **Plan + 11 supporting documents** (#1174) — 4 independent proposals, 3 validation
  audits, 2 syntheses, 2 fact-base docs.
- **P0** `MEMORY.md` eviction (#1177) — 17 closed rows; horizon **~23 → ~32 days (+9)**.
- **P1** worktree ancestor canary (#1177) — content-dedup **confirmed**.
- **P2** budget gate + ratchet (#1178) — `util/memory_budget_check.py`, 22 tests.
- **G3** relocation completeness (#1179) — `util/relocation_check.py`, 19 tests.
- **P3.1–P3.4** the cut (#1180, #1182, #1187, #1188) — `AGENTS.md`
  **168,317 → 45,084 chars** (170,137 → 45,307 bytes).
- **P4** gate BLOCKING (#1190) + `Memory Budget` a **required context** in ruleset
  `13805432` (15 → 16). Helper preserved (#1191).
- **P0b** worktree prune (#1194) — 7 removed. **Only the prune half; see item 6.**
- **Resident hazards restored** (#1196) — P3 dropped a required carve-out; now
  `AGENTS.md` **43,720 chars**, 1,364 under ceiling.
- Two live defects fixed (#1175); one corruption repaired (#1185).

### Remaining work

**0. Task zero — the primary checkout is stale, and archiving this file.**
`/home/pcalnon/Development/python/Juniper/juniper-ml` was left at `dfbca13`, behind
`origin/main`. That is not cosmetic: by P1 a *differing* ancestor makes every
worktree session load a second full `AGENTS.md`, and `AGENTS.md` worktree-cleanup
**Phase 7** requires restoring it after every merged-PR cleanup. Also, `notes/`
§4b and `util/ad-hoc/2026-08-20_worktree_liveness_probe.py` **do not exist** at that
commit — a session reading the plan there will think P3/P4/P0b never shipped.
Fix first: `git fetch origin && git pull --ff-only origin main`.

**1. P5 — fleet rollout.** **Order is mandatory (plan correction C1): rate axis
before level axis.** A ceiling set *after* a cut locks in the inflated level, and a
level fix without a rate fix is undone in ~44 days — that is how `AGENTS.md` reached
170K *while under four active CI gates* (172 of 200 merges grew it; 14 shrank it, by
2,628 bytes total). Do **not** take "canopy is 93K, big win first".
Targets: `juniper-canopy` (93,151 chars) and `juniper-cascor` (68,224), then the
other 7. **File a tracking issue per repo — none exists.** Per repo:
- **a.** Converge that repo's worktrees (item 6) — zero authoring cost.
- **b.** Copy `util/memory_budget_check.py`, `tests/test_memory_budget_check.py`,
  `conf/memory_budget.json`. **Seed the ceiling by running
  `python util/memory_budget_check.py --ratchet` in the target repo — never by
  transcribing a number from a note.** Both scripts take `--repo-root` and are
  already repo-agnostic.
- **c.** Copy the standalone `memory-budget` job from `ci.yml`. Standalone, **not** in
  the Quality Gate `needs:` (correction C9).
- **d.** Soak `--advisory` first, then remove it, then run negative controls (clean
  exit 0 / +500 chars exit 1 / waiver exit 0 — *a blocking gate that cannot fail is
  worse than none*), then promote:
  `python3 util/ad-hoc/2026-08-20_add_required_context.py --repo pcalnon/<repo> --ruleset-id <ID> --context 'Memory Budget' --apply`
  (dry-run by default; find `<ID>` via `gh api repos/pcalnon/<repo>/rulesets`).
- **e.** Then G3, then the cut via `util/ad-hoc/2026-08-19_p3_relocate_section.py`.
  **`juniper-cascor` has no `docs/REFERENCE.md`** — create the destination first.
- **Migration-order trap (P1, recurs per repo):** the cut must land on that repo's
  `main` **with its primary checkout pulled** before any worktree carries the trimmed
  file. Trimmed worktree + untrimmed ancestor is the *worst* case — context goes **up**.

**2. Parent `Juniper/AGENTS.md`** — 11,016 **bytes**, additive to every session in all
9 repos, in a directory that is **not a git repo** (no VCS, no CI, no gate). Owner
decision #8 says "yes, separately" and picks no approach, so **the first action is an
owner question, not an edit**: (a) `git init` the parent so it can carry a gate,
(b) hand-cut it to a pure index, or (c) push content down into the 9 repo files.

**3. `MEMORY.md` forward-only cap** (correction C7; owner decision #4 = 120 bytes on
**new** entries, no rewriting existing rows). Eviction shipped; the cap did not.
Now 124 lines / 17,209 bytes against a hard **200-line / 25,000-byte** cap that
truncates **silently, newest-first**. **The blocker is that there is no enforcement
surface**: the file lives outside every repo
(`~/.claude/projects/…/memory/MEMORY.md`), so no CI job can reach it. Pick an
approach before writing code — a `util/` linter, a local hook, or documented
discipline. Eviction bought only **+9 days**, and rows cluster at 173–215 chars
against a 146.7 mean, so compression cannot close the gap: this needs **recurring**
curation (`util/ad-hoc/2026-08-19_memory_index_evict.py`). Hard rule: **detail may be
demoted; STATUS may not** — a row reading "all CLOSED" over an open blocker is worse
than omission.

**4. Worktree settings asymmetry — a constraint, not yet a task.** The main checkout
has an active `.claude/settings.local.json` (1,801 B, read by Claude Code); it is
gitignored at `.gitignore:167` so it does **not** travel into worktrees. This only
becomes work if a settings-based remedy (`claudeMdExcludes`, hooks) is chosen for
items 2 or 3 — and note plan §7.5: any `.claude/` destination is **outside the docs
content-loss screen entirely**.

**5. The soak (plan §6) — build the instrument first; it cannot start without one.**
N ≥ 20 sessions testing whether agents retrieve relocated facts when relevant.
Neither the plan nor this handoff defines how a miss is recorded, so task one is a
ledger (suggest `notes/JUNIPER_<date>_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`; one
row per session: date, task, fact needed, followed Y/N, which pointer), a start
marker (count from `500508b`), and a definition of "miss". Ladder, fixed in advance:
*index row → CI gate or hook → path-scoped rule*. **Never re-inline** — that is how
the file reached 170K. Caveat (plan §7.6): a path-scoped rule is **lost at
compaction**. Owner decision #7 keeps Proposal A's Skills as an optional later probe
if the soak shows a real problem.

**6. The level axis is not closed, and P0b is half-done.**
`AGENTS.md` is 43,720 chars against owner decision #2's target of **32,443**
(still recorded in `conf/memory_budget.json` as `"Target after P3: 32443"`). Per-PR
return has fallen — the remainder is many small sections — but candidates remain.
Separately, P0b specified *"prune merged worktrees **and rebase the rest so their
`AGENTS.md` converges**"*; only the prune shipped. Converging is free and still owed:
`git -C <worktree> merge origin/main` recovers ~44K chars per session per worktree,
with no content edit and no risk.

### Key context — read before acting

- **Worktree population is not a fixed number — re-measure, never trust a count in a
  document.** It moved 23 → 24 *during* the P0b sweep. The remedy for a diverging
  worktree is to **converge it, not remove it**. Removal requires all four gates in
  order: `scripts/cleanup_session_worktrees.py --dry-run` (merged + clean + not-cwd,
  fail-closed) → re-run it immediately before acting → the liveness probe → remove
  **individually, never `--force`**. The probe is a supplement, not a substitute:
  `python3 util/ad-hoc/2026-08-20_worktree_liveness_probe.py <path> …` (exit 0 none
  occupied / 1 occupied); **a hit is a hard stop, `clear` is corroboration, NOT
  proof** — a session idling elsewhere while holding the worktree open is invisible
  to it, as is any `/proc` entry it cannot read. Treat `locked` as a stop.
- **`@path` imports save ZERO tokens** — eagerly inlined at launch. Any design
  resting on them is void.
- **Nothing is truncated** except `MEMORY.md`. The "character limit" is a per-file
  *warning* at `max(40000, round(r × 0.05 × chars_per_token))` — `r` is *believed*
  to be the context window (fact base §8 lists this as **unverified**). The real hard
  limit is 4 MiB and it **skips the file whole**.
- **The docs screen cannot see a relocation** — its FAIL predicate needs
  `added == 0`, so "delete a block, leave a pointer, keep the heading" is a WARN at
  any magnitude. **G3 is the content-loss control — but it runs `--advisory` in CI
  and does not exist post-merge. A green PR proves nothing about content loss; the
  local run is the control.** Use `--expect-removals` on relocation PRs only (it
  hard-fails, exit 2, on a PR that removes nothing).
- **G3 and the docs screen are complementary.** G3 skips headings; the docs screen is
  blind to prose-dropped-but-identifiers-kept. P3.4 needed both.
- **G3 does not check *placement*.** #1196: P3 relocated four hazards the plan
  required to stay resident; G3 confirmed they arrived and reported nothing wrong.
  **`AGENTS.md` now has a `## Hazards` section that may not be relocated** — adding a
  hazard means ratcheting space out of a reference section in the same PR, not waiving.
- **Relocate by script, byte-for-byte** (`util/ad-hoc/2026-08-19_p3_relocate_section.py`)
  so G3 passes *by construction*. It rewrites relative links and **the order is
  load-bearing** — rationale at `:54-73`; running them out of order silently redirects
  every destination anchor back at the source.
- **G3 caught two losses human judgement had already approved** (#1185, #1188). Trust
  the gate over the instinct.
- **Verify a merge's cumulative `origin/main..HEAD` delta, never the tip commit's.**
  #1183 reverted P3.2 through a *merge commit* while adding 7 copies of chat
  transcript; its tip showed **+2 bytes**. The per-PR budget gate is the defence
  (base-tip comparison ⇒ over-ceiling + grew); **there is no post-merge size check**.
  `gh pr list` before opening anything.
- **The budget ceiling is itself ungated.** Raising `ceiling_chars` in
  `conf/memory_budget.json` passes the check — the downward-only ratchet is defeated
  by one line. Treat a diff touching that file as a policy change requiring the owner;
  adding a base-vs-head ceiling comparison is the first P5 hardening item.
- **The two waivers are different species.** `Allow-Docs-Rewrite:` is a one-shot
  per-range demotion — attach only after the screen fires **and** G3 `--expect-removals`
  reports `unmatched=0`. `Allow-Budget-Overrun:` is a **loan**: the ceiling does not
  move, so the debt blocks the next author. It has **no** false-alarm class, so use it
  for genuinely warranted growth, record why in the PR body, and open the relocation
  issue in the same breath. **No central ledger exists** (plan §7.7 admits this is
  specified but unsolved). Carry trailers into the **squash** message.
- **`AGENTS.md` headroom is 1,364 chars** under a blocking, required gate. Additions
  relocate to `docs/REFERENCE.md` with a pointer that keeps an accurate open/closed
  status.
- **The UTC/local day gap** bites `Verify AGENTS.md Last Updated` on any PR authored
  after ~19:00 CDT. Set the header to today's **UTC** date.
- **Never pipe an exit-code-significant command through `tail`** — use
  `set -o pipefail` or read `${PIPESTATUS[0]}`. `util/safe_merge.py` **defaults to
  dry-run**; `--execute` is required or it silently does nothing.
- **Plan §7 lists seven residual risks; this handoff carries four.** Re-read §7
  before the rollout.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git pull --ff-only origin main   # PRIMARY CHECKOUT WAS LEFT BEHIND
git log --oneline -1                  # expect 500508b (#1196) or later
wc -m -c AGENTS.md                    # expect 43720 chars / 43935 bytes
python3 util/memory_budget_check.py   # expect OK, headroom=1364, exit 0
python3 -m unittest tests/test_memory_budget_check.py tests/test_relocation_check.py
                                      # expect Ran 41 tests ... OK
gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
  --jq '[.rules[]|select(.type=="required_status_checks")
        |.parameters.required_status_checks[].context]|length'   # expect 16
grep -c 'KILL_WORKERS' AGENTS.md      # expect 1 — the resident hazard list
git worktree list | wc -l             # re-measure; do NOT trust any count in this file
# then create a worktree; do not work in the primary checkout
```

### Full local pre-flight (run all of it before every push)

```bash
pre-commit run --files <every changed path>
juniper-symbol-loss-check   --base origin/main --head HEAD \
    --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'
juniper-docs-additions-check --base origin/main --head HEAD
python3 util/relocation_check.py --base origin/main --head HEAD \
    --source AGENTS.md --dest docs/REFERENCE.md --expect-removals   # relocation PRs only
juniper-check-doc-links --exclude templates --exclude history --exclude legacy \
    --exclude pull_requests --exclude releases --exclude analysis --exclude fixes \
    --exclude development --exclude CHANGELOG.md --cross-repo skip
python3 -m unittest tests/test_memory_budget_check.py tests/test_relocation_check.py
python3 util/memory_budget_check.py
```

Running a subset failed twice in the origin session. `--expect-removals` is the one
thing CI does **not** do.

### Git status at handoff

- Branch `docs/handoff-shared-session-memory`, worktree `swirling-kindling-octopus`.
- `origin/main` at `500508b` (#1196). **No open PRs in juniper-ml.**
- **The primary checkout is at `dfbca13`, behind `origin/main` — pull it first**
  (see item 0). Worktree-cleanup Phase 7 was not run.
- Worktree count moves hourly; re-measure. Most divergence is **active work**;
  several still carry pre-cut `AGENTS.md` copies and should be **converged**.

---

## Provenance

Origin session ran problem investigation through full execution: 11 agents
(2 fact-finders, 4 proposal authors, 3 validators, 2 synthesists), then 15 merged
PRs. This handoff was audited by three independent validators before archiving —
they found 1 CRITICAL + 2 FATAL and ~20 lesser defects in the first draft, including
a bytes-labelled-as-chars figure that would have seeded sibling ceilings ~1,900 chars
too high, and a stale-count line that authorised removing live worktrees. Handoffs
inherit errors across generations; validate the next one the same way.
