# HANDOFF 2026-09-04 — partition arc CLOSED, five fix tickets merged, only X_full removal left

**UNVERIFIED** — written to a token budget, no independent validation pass run. Treat every
figure as needing re-derivation before it is relied on. Verification commands in §5.

Documents referenced (name them in your own summaries — mandatory convention, `Juniper/AGENTS.md`
§ Cross-Project Conventions):

- design of record: `juniper-ml/notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`
- implementation plan: `juniper-ml/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`
- review protocol: `juniper-ml/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`

---

## 1. Goal

Implement **required-fix 0** of §9.6.4 of the design of record: **remove `X_full` and the whole
`*_full` family from the contract** (decision 11, §9.5). It is the only fix left and the only
cross-repo one. Read §9.5 and §9.6 of the design of record BEFORE anything else — §§9.3 and 9.4 are
marked HISTORY and will mislead you.

## 2. What closed (all merged, ancestry-verified)

**Partition design — the question is settled.** Decisions 1–8, 11, 12 settled; 6 retired; **9
REVERSED** (both P-1a and P-1b abandoned); **10 COLLAPSED** (no guard needed). Partitions come from
`shuffle_and_split` / `temporal_split_index` and are **index-disjoint by construction**.

The arc's net effect on the partitioning mechanism was **zero code change**: it established the
shipped behaviour was already correct, and that four proposed improvements (P-1a, P-1b, the guard,
the row-reuse gate) would each have made things worse or caught nothing.

| PR | repo | what |
| --- | --- | --- |
| ml#1546 | juniper-ml | decisions 6–8 |
| ml#1553 | juniper-ml | P-1a measured BLOCKED |
| ml#1554 | juniper-ml | round-3 findings verified; R-4 downgraded |
| ml#1560 | juniper-ml | decision 9 (P-1b) + class scope limit |
| ml#1562 | juniper-ml | class-1 census; G-b overturned |
| ml#1568 | juniper-ml | two proposals + consensus review (§9.4) |
| ml#1585 | juniper-ml | decision 11 — drop `X_full` |
| ml#1595 | juniper-ml | decisions 9 REVERSED / 10 COLLAPSED / 12 (§9.6) |
| ml#1599 | juniper-ml | row-reuse gate dropped |
| cascor#616 | juniper-cascor | inline test-partition ingress |
| data#322 | juniper-data | seed defaults (#319) |
| data#323 | juniper-data | normaliser fit scope (#314) |
| data#333 | juniper-data | circular import (#316) |
| data#343 | juniper-data | Postgres model-derived schema (#320) |

**All five fix tickets are closed.** #317 was fixed in parallel by a peer (data#318). juniper-data
unit suite: **1253 → 1358 passing**.

## 3. Remaining work — `X_full` removal

§9.5.4 of the design of record scopes it. Four items, none started:

1. **`DatasetMeta.n_samples`** is `len(X_full)`, asserted by `test_e2e_metadata_consistency` →
   redefine as the partition sum.
2. **canopy's ONLY artifact validation ladder validates `X_full`** (`juniper-canopy/src/demo_mode.py:821-837`).
   Re-point it or the guard is **silently lost**. Do this deliberately and test it.
3. **The data-client preview** serves the first *n* rows of `X_full` → needs a new source; `train`
   changes semantics slightly.
4. **`NPZ_SPLITS`** (`juniper-data-client/juniper_data_client/constants.py:421`) is
   `("train","test","full")` → drop `"full"`, add `"val"`. One coherent edit; resolves **S-3** in §9
   of the implementation plan.

**Backward compatibility:** all stored artifacts carry `X_full`. Consumers must keep *tolerating*
it; only the requirement is dropped. `juniper-cascor/src/spiral_problem/data_provider.py:193`'s
`required_keys` is the one site that would reject its absence.

**Consumer census (§9.5.1)**: every use is "give me the whole dataset", never "the array the
partitions were cut from". Nothing indexes it with partition-derived indices. In the equities
artifact all five `*_full` arrays already have `_train`/`_test` siblings.

**Not covered by that census:** anything outside the eight repos; whether `date_*` /
`ticker_code_*` / `y_reg_*` need a `_val` sibling; the sequence tier's `t_*` / `dt_*` /
`observed_mask_*` families.

## 4. Traps confirmed this session

1. **`pre-commit run --all-files` skips UNTRACKED files.** `git add -A` first, or CI lints a file
   you never did.
2. **Subprocess tests earn no coverage credit.** Bit me three times — the per-file gate is ≥90%.
   When a property genuinely needs a subprocess (import cycles, import-time env resolution), add
   in-process tests for the same lines or the gate fails.
3. **The sequence-safety waiver value is a WHITESPACE-SEPARATED SYMBOL LIST, not prose.** A
   justification sentence is tokenised into words, matches nothing, and the screen still fails.
   Rationale goes in the commit BODY. See `reference-sequence-safety-local-repro` memory.
   Extract-and-derive trips it routinely even when capability increases.
4. **A `# nosec` on a `return f"""` line lands INSIDE the string** and silently corrupts the
   generated value. Bind first, annotate the closing line.
5. **`git checkout <file>` restores from the INDEX** — it wipes uncommitted work. Commit before
   mutation-testing.
6. **CodeQL review blocks merge while all checks read green** (`mergeState=BLOCKED`, no FAILURE).
   Check `gh pr view --json reviews`.
7. **`--auto` does not merge here**; `BEHIND` needs an explicit `gh api -X PUT .../update-branch`.
8. **gh 2.46.0 breaks `gh pr edit`** — amend via a PR comment instead.

## 5. Verification

```bash
# Design state — §9.6 must exist and say the question is closed
git -C juniper-ml show origin/main:notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md \
  | grep -c "partitioning question is CLOSED"      # 1

# All five fix tickets closed
gh issue list --repo pcalnon/juniper-data --state all --limit 20 --json number,state \
  --jq '.[] | select(.number|IN(314,316,317,319,320)) | "\(.number) \(.state)"'   # all CLOSED

# juniper-data suite
cd juniper-data && /opt/miniforge3/envs/JuniperData/bin/python -m pytest juniper_data/tests/unit/ -q   # 1358 passed

# X_full still present everywhere (nothing removed yet)
grep -rn "X_full" --include=*.py juniper-data/juniper_data/generators/spiral/generator.py | head -2
```

## 6. Git state

- **juniper-ml session worktree** `.claude/worktrees/shimmering-booping-pebble`, branch
  `worktree-shimmering-booping-pebble`, clean, rebased onto `origin/main` at `42d33634`. Drifts
  behind continuously — peers merge into this repo constantly; re-fetch, do not assume.
- **juniper-data** primary clean at `0daf00b`. All task worktrees removed.
- Environments: `/opt/miniforge3/envs/JuniperData/bin/python` for juniper-data;
  `/opt/miniforge3/envs/JuniperCascor1/bin/pre-commit` runs hooks for both.

## 7. Open, not blocking

- **Round 2 of the §9.4 consensus review is owed and UNRUN.** Moot for decisions 9/10 (ruled
  directly); still owed for §9.4's other content.
- **A degeneracy-ratio check is uncovered by anything** — deliberate, recorded in §9.6.4. It would
  catch `xor(margin=x_range=y_range)` producing 4 distinct rows of 200. No action implied.
- **juniper-data has no empty-dataset check at the API/core layer** — data#318's backstop is
  per-generator. Noted on data#317, not filed.
- **canopy#559** — stale-env justification for a hand-rolled probe. Untouched.
- `MEMORY.md` is ~22KB against a 17.1KB target; the hook flags it on every write. Needs a
  deliberate compaction pass; a peer session was active in that area.
