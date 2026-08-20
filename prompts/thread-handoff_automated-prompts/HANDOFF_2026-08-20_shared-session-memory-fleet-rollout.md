# HANDOFF — Shared Session Memory: fleet rollout and residual work

**Date**: 2026-08-20
**Origin session**: shared session memory (juniper-ml)
**Branch at handoff**: `docs/handoff-shared-session-memory` (worktree `swirling-kindling-octopus`)

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** effort in `juniper-ml`. The plan is
[`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md);
its §4a/§4b execution log is authoritative for what already shipped. **All plan
phases are complete.** What remains is fleet rollout plus five residual items.

### Completed so far (13 PRs, all merged)

- **Plan + 11 supporting documents** (#1174) — 4 independent proposals, 3 validation
  audits, 2 syntheses. Fact base:
  [`…MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md)
  and [`…CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md).
- **P0** `MEMORY.md` eviction (#1177) — 17 closed rows evicted; horizon ~19 → ~32 days.
- **P1** worktree ancestor canary (#1177) — content-dedup **confirmed**.
- **P2** budget gate + ratchet (#1178) — `util/memory_budget_check.py`, 22 tests.
- **G3** relocation completeness (#1179) — `util/relocation_check.py`, 19 tests.
- **P3.1–P3.4** the cut (#1180, #1182, #1187, #1188) — `AGENTS.md` **170,137 → 45,084 chars**.
- **P4** gate promoted to BLOCKING (#1190) + `Memory Budget` added as a **required
  context** in the `juniper-ml-rules` ruleset (15 → 16). Helper preserved (#1191).
- **P0b** worktree hygiene (#1194) — 7 stale worktrees removed (24 → 17).
- Two live defects fixed (#1175); one corruption repaired (#1185).

### Remaining work

1. **P5 — fleet rollout.** `juniper-canopy` (94,373 chars) and `juniper-cascor`
   (70,118) are on the same trajectory across 9 repos. Port in this order:
   the budget gate + ratchet first (rate axis, satisfiable immediately, needs no
   destination), then G3, then the cut. `tests/test_agents_md_header_schema.py` is
   the precedent for portable, self-locating lints.
2. **Parent `Juniper/AGENTS.md`** — 11,016 fully-additive bytes loaded by every
   session in all 9 repos, in a directory that is **not a git repository** (no VCS,
   no CI, no gate, no review). Nothing in the plan reaches it. Verify with
   `git -C /home/pcalnon/Development/python/Juniper rev-parse` → fails.
3. **`MEMORY.md` forward-only cap.** Plan correction C7 was *evict, then cap*.
   Eviction shipped; the 120-byte cap on **new** entries did not. Eviction alone
   buys ~+9 days, so this is the durable half. Current: 124 lines / 17,209 bytes
   against a hard 200-line / 25,000-byte silent-truncation limit.
4. **Worktree settings asymmetry.** The main checkout has an active
   `.claude/settings.local.json` (1,801 B, read by Claude Code); it is gitignored at
   `.gitignore:167` so it does **not** travel into worktrees. Sessions in worktrees
   run without settings main-checkout sessions get. Any settings-based remedy
   (`claudeMdExcludes`, hooks) must reach worktrees.
5. **The soak (plan §6).** N ≥ 20 sessions to falsify the pointer-follow bet, with a
   fixed ladder: *index row → CI gate → path-scoped rule*, **never re-inline**.
   Re-inlining is how the file got to 170K.

### Key context — read before acting

- **`@path` imports save ZERO tokens.** Eagerly inlined at launch; official docs say
  so three times. Any design resting on them is void.
- **Nothing is truncated.** The "character limit" is a per-file *warning* at
  `max(40000, ctx×0.05×chars_per_token)`. The real hard limit is 4 MiB and it
  **skips the file whole**. `MEMORY.md` is the only thing that truncates, and it does
  so **silently, newest-first**.
- **The docs screen cannot see a relocation.** Its FAIL predicate needs
  `added == 0`, so *"delete a block, leave a pointer, keep the heading"* is a WARN at
  any magnitude. **G3 is the only content-loss control for a cut.** Run it with
  `--expect-removals` so it cannot pass vacuously.
- **G3 and the docs screen are complementary, not redundant.** G3 skips headings;
  the docs screen is blind to prose-dropped-but-identifiers-kept. P3.4 needed both.
- **Relocate by script, byte-for-byte** (`util/ad-hoc/2026-08-19_p3_relocate_section.py`)
  so G3 passes *by construction*, not by the author's judgement. It rewrites relative
  links; **the rewrite order is load-bearing** (source-internal anchors first).
- **G3 caught two real losses that human judgement had approved** — 4 lines of a
  concurrent session's docs during a repair, and 4 more in P3.4 where a table
  "obviously" superseded prose it did not carry. Trust the gate over the instinct.
- **Merged-and-clean does not mean idle.** Before removing any worktree run
  `util/ad-hoc/2026-08-20_worktree_liveness_probe.py`; on first use it caught a
  worktree passing every gate while a live session held it. Never `--force`.
- **Concurrency is the disease.** #1183 reverted P3.2 through a *merge commit* while
  adding 7 copies of chat transcript; its tip commit showed a **+2 byte** delta.
- **The full pre-flight is non-negotiable**: pre-commit **and** both sequence-safety
  screens **and** G3 **and** doc-links **and** the gate tests. Running a subset failed
  twice in the origin session.
- **`AGENTS.md` has zero headroom** (45,084 / 45,084) under a now-blocking, required
  gate. Additions must relocate to `docs/REFERENCE.md` and leave a pointer that keeps
  an accurate open/closed status — *detail may be demoted; status may not*.
- Waivers (`Allow-Budget-Overrun:` / `Allow-Docs-Rewrite:`) are **loans**: the
  ceiling does not move. Attach one only after the gate has actually fired **and**
  there is independent evidence it is a false alarm. Carry it into the **squash** message.
- The UTC/local day gap bites `Verify AGENTS.md Last Updated` on any PR authored
  after ~19:00 CDT. Set the header to today's **UTC** date.
- Never pipe an exit-code-significant command through `tail` — it masks the status.
  `util/safe_merge.py` is the merge path; check its real exit code.

### Verification commands for the new thread

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -1                  # expect c1589cd or later
wc -c AGENTS.md                       # expect 45,307 bytes / 45,084 chars
python3 util/memory_budget_check.py   # expect OK, exit 0
python3 -m unittest tests/test_memory_budget_check.py tests/test_relocation_check.py
gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
  --jq '[.rules[]|select(.type=="required_status_checks")
        |.parameters.required_status_checks[].context]|length'   # expect 16
```

### Git status at handoff

- Branch `docs/handoff-shared-session-memory`, worktree `swirling-kindling-octopus`.
- `main` at `c1589cd`; working tree otherwise clean.
- Open PR not owned by this effort: **#1195** (snapshots retraction, another session).
- 17 worktrees remain; 15 still diverge from main and are legitimately in use
  (dirty or unmerged) — they are active work, not cleanup targets.

---

## Provenance

Origin session covered problem investigation through full execution: 11 agents
(2 fact-finders, 4 proposal authors, 3 validators, 2 synthesists), then
implementation. This handoff was validated by independent custom agents before
archiving, per the standing rule that handoffs inherit errors across generations.
