# HANDOFF — decision 11 is merged everywhere and released nowhere

**Date**: 2026-09-07 · **Session**: <https://claude.ai/code/session_01LEko3Vu7hbd8fekk9ExrAF>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-tumbling-puppy`
**Branch**: `docs/decision-11-shipped` (juniper-ml#1808, open) · juniper-ml#1807 MERGED 14:28:23Z
**Revision**: consensus-validated, 5 agents / 1 round. §11 records the **19 corrections** the review
forced — **eight of them errors this document's own first draft introduced**, including one that
wrongly "refuted" its predecessor and one that made the document contradict itself two sections
apart.

**Documents REFERENCED** (the ecosystem convention in
`/home/pcalnon/Development/python/Juniper/AGENTS.md` § Cross-Project Conventions requires the
filename on every citation, because more than one document is cited):

- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` — design of record
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` — rollout plan; **§9 is
  the live register, §§2–7 are pre-review and NOT folded back**
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — §11's instrument
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` — this document's template
- `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` — §11, the release ceremony
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-05_partition-arc-decision-11-and-the-ninth-repo.md`
  — predecessor. **Still worth reading**: its §4 (canopy), §6.1 (row order) and §13 (traps) carry
  detail this document compresses.

**Documents CHANGED by this session**: `/home/pcalnon/Development/python/Juniper/AGENTS.md`
(unversioned), `juniper-ml/AGENTS.md`, `juniper-ml/docs/REFERENCE.md`,
`juniper-ml/docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`,
`juniper-ml/reports/2026-09-05_canopy-deadlock-consensus/laneB1.md`, and this file.

---

## 0. PREFLIGHT

1. **Decision 11 is MERGED. It is RELEASED NOWHERE** — every package's `main` is *ahead* of its
   latest tag (§4). The single most important consequence:
   **`POST /v1/crossval` is still broken in any PyPI-installed deployment** — the fix lives in
   `juniper-recurrence-model`, and `juniper-recurrence/juniper-recurrence/pyproject.toml:51` pins
   `juniper-recurrence-model>=0.1.5,<0.3.0`, whose newest release (`-v0.2.0`, 2026-07-29) predates
   juniper-recurrence#150 (2026-09-06). The release train is not hygiene; it is what makes the fix
   real.
2. **`juniper-recurrence/README.md` is AMBIGUOUS and it cost this document a wrong refutation.**
   The repo `pcalnon/juniper-recurrence` **contains a subdirectory also called
   `juniper-recurrence/`**. The repo-root `README.md` has zero `_full` hits; the *subdirectory*
   `juniper-recurrence/README.md:48` has one. The first draft greped the root, and on that basis
   declared the predecessor's (correct) claim "refuted". The same shape applies to
   `juniper-recurrence-client/` and `juniper-recurrence-model/` — they are **subdirectories, not
   repos**; `gh api repos/pcalnon/juniper-recurrence-client/...` returns 404.
3. **cascor's val refusal is TWO rules and only one is overridable.** `_resolve_validation_split`
   (`juniper-cascor/src/api/lifecycle/manager.py:3618`): rule 3 at **`:3649`** — neither val nor
   test — is **NOT overridable** ("no switch re-enables it", docstring `:3634-3636`). Rule 2 —
   val absent, test present — raises at **`:3657`** and honours
   `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT`; `:3658` is the message string, which is what a
   grep returns. **Both rules are reachable only from `_reload_dataset`** (`:3885`, via `:4004`) and
   `app.py:532` — the inline-data path `routes/training.py` → `start_training(X_val=None)` **bypasses
   the gate entirely**.
4. **Local checkouts are stale.** `/home/pcalnon/Development/python/Juniper/juniper-data` was found
   at `005a82b`, predating #369. Fetch, or read `origin/main` via
   `gh api repos/O/R/contents/<path>`. **§7's commands do this for you — use them.**
5. **Environment** (dropped by the first draft, restored — the always-loaded parent `AGENTS.md` was
   corrected this session but other machines will not see it, §8): conda envs are
   **`JuniperCascor1` / `JuniperCanopy1` / `JuniperData`** — the unsuffixed names are
   `-DEPRECATED` on disk. **juniper-recurrence has no conda env**; install into the active one.
   juniper-data is **not running** (port 8100 idle). canopy python needs `env -u LD_LIBRARY_PATH`.
6. **Status transcribed from a document is not status.** The predecessor was burned by this (four
   juniper-data issues read "filed, none started" in the design doc; GitHub had closed them days
   earlier). Every disposition below was re-derived from code, git or the API. Do the same before
   trusting §3 or §5.

---

## 1. Goal statement

Decision 11 — removing the `*_full` family from the NPZ contract — merged as **eight PRs across six
repositories, 2026-09-05 → 09-06** (half of them on the 5th; a log filtered to 09-06 loses four).
What remains is **a release train that is currently the difference between a fixed bug and a broken
one** (§4), **nine straggler sites** (§3), **five carried-forward risks and two unfinished chunks**
(§5), and **two unimplemented decisions** — 12 and **5**.

**Merged and verified on `main`** — each checked by reading the file on `origin/main`, never the
MERGED badge:

| repo | PR | merged (UTC) | what landed |
| --- | --- | --- | --- |
| juniper-ml | #1585 | 09-03 00:58 | design doc only — the decision itself, no code |
| juniper-data-client | #187, **#190** | 09-05 12:37 | `NPZ_SPLITS = ("train","val","test")` (`constants.py:437`) |
| juniper-canopy | #586, **#589** | 09-05 19:55 | validation ladder → `_VALIDATED_PARTITIONS` |
| juniper-recurrence | **#150** | 09-06 00:34 | `derive_full_split` (`…-model/…/data.py:67`) |
| juniper-cascor | **#625** | 09-06 00:45 | `required_keys` relaxed (`data_provider.py:219`), tuple 4→3 (`:255`) |
| juniper-data | **#369** | 09-06 10:37 | producer stops emitting; 16 generators → `VERSION 3.0.0` |
| juniper-ml | **#1805** | 09-06 10:50 | `_whole_dataset` (`snapshot_attribute.py:291`, called in-try `:342`) |

**Required-fix 0 (design §9.5.4) is CLOSED, all four**, each verified in the sibling repo:
(1) `n_samples = n_train + n_val + n_test` — `juniper_data/core/meta.py:66`; (2) canopy
`_VALIDATED_PARTITIONS`; (3) preview serves `X_train` — `api/routes/datasets.py:971`;
(4) `NPZ_SPLITS` as above.

**Open**: juniper-ml#1808 (this branch) — flips `docs/REFERENCE.md` + the cheatsheet from "decision 11
is NOT implemented" to what shipped. Armed, regression tests pending. **#1807 merged** — it made the
parent-guide link a code span, because in CI **only juniper-ml is checked out**, so `../CLAUDE.md`
does not exist on disk. (That the parent directory is not a git repo is a *separate* fact, §8; it is
not why the link fails, and making it a repo would not fix it.)

**Next actions, in order.** (1) Land #1808. (2) **Execute §4** — until then the arc is unreachable
from PyPI and crossval stays broken. (3) §3's stragglers, starting with S-6 (canopy silently renders
train-only). (4) §5's carried risks and Chunks 5 / 7. (5) Decision 12 is a design task; start at
§9.6.3 / §9.6.6 of the design document, which record the schema as *described, not specified*.

**Decision 5 is ALSO unimplemented, and this document's own PREFLIGHT 3 is the evidence.** Design
`:371` rules *"Should the CLI early-stop? Yes … The CLI gains `eval` and early stopping."*
`juniper-cascor/src/main.py` contains **zero** occurrences of `X_val` / `x_val` / `val_x`, and
`_resolve_validation_split` is reachable only from service paths. "The direct CLI tolerates a
val-less artifact" is not merely back-compat — it is decision 5 not having shipped. Design §9.1 also
still carries **V-2** and **V-3** open, V-3 being decision 5's own measurement.

---

## 2. The invariant, and its two exceptions

1. **Never REQUIRE `X_full`.** Nothing **in the generator path** emits it — `partition_and_assemble`
   returns six keys and all 16 generators are at `VERSION 3.0.0`. **`hf_store` and `kaggle_store`
   still do** (S-1), so this is not a universal. Build the whole dataset by concatenating the
   partitions **in `train | val | test` order** — the order `juniper_data/core/split.py` used
   (`np.vstack([X_train, X_val, X_test])`).
2. **Never assert `X_full` is ABSENT.** Every artifact stored before 2026-09-06 carries it and
   design §9.5.4 obliges consumers to keep loading those.
3. **A concatenating whole-view helper must tolerate an absent `X_val`.** HF/Kaggle artifacts have
   no val partition at all, so a bare three-way concat raises `KeyError` on exactly the artifacts
   S-1 says are still being produced.

**The two exceptions — and they are NOT the same kind of exception.** Both `equities` and
`equities_seq` built `_full` **entity-major** (each ticker's train, val, test in turn) while their
partitions are **split-major**. Anything slicing the whole view **by row index** — walk-forward CV
does — gets different folds. But the reconstructions differ in a way that matters:

- **`equities_seq` — a pure PERMUTATION, exactly reconstructible.** `_assemble` builds `full` from
  the same per-ticker split blocks (`generators/equities_seq/generator.py:236-239`), so stable-sorting
  the concatenation on `ticker_code` recovers it row for row.
- **`equities` — a strict SUPERSET, and reconstruction is LOSSY.**
  `generators/equities/generator.py:335` is `full_frames.append(frame)` — **the entire frame** — while
  the partitions are ratio-bounded slices (`:331-334`). `generators/equities/params.py:143` rejects
  only ratio sums **above** 1.0, so a legal `train=0.6 / val=0.2 / test=0.1` leaves 10% of every
  ticker's rows in `full` and in **no** partition; `int(round(...))` down-rounding does the same even
  at ratios summing to 1.0. **No reordering can recover rows that are in no partition.** A
  concatenation is a lower bound on the legacy array — assert its length, never assume it.

**Two consumers reconstruct that view, and only one handles the asymmetry:**

- `juniper_recurrence_model.data.derive_full_split` — concatenates, then **stable-sorts on
  `ticker_code`**, recovering entity-major order. Correct **for `equities_seq`**; still a lower
  bound for tabular `equities`.
- **juniper-canopy `src/demo_mode.py:881-887` `_whole_dataset` — prefers a legacy `*_full`, else
  concatenates, with NO reordering** and no `ticker_code` at that layer. Reached at `:1016-1017`
  and `:1919-1920`. Tabular `equities` is 2-D and **does** reach it. So canopy renders **two
  different row orders for the same logical dataset depending on artifact vintage**. Unfixed.

---

## 3. Stragglers — nine sites, and the instrument that enumerates them

**Use the committed census instrument rather than a fresh grep**:
`util/ad-hoc/2026-09-05_census_full_family_v2.py` (11 scopes incl. the ecosystem root, 8 file types,
`git ls-files`). Current totals — PRODUCE / CONSUME / ASSERT / PROV / files:

```
juniper-data 8/92/487/21/77 · juniper-data-client 1/15/33/1/13 · juniper-cascor 0/25/78/24/20
juniper-canopy 0/17/74/4/22 · juniper-recurrence 0/52/44/1/13 · juniper-deploy 0/6/0/0/1
juniper-ml 0/41/9/513/101 · <ecosystem root> 0/12/0/0/2 · cascor-client/worker/slacker all zero
```

It **over-reports** by design (juniper-deploy's six are `profiles: ["full", …]` in
`docker-compose.yml`); the false-positive class is documented in the script. Predecessor §3.1
diagnosed the failure this replaces: *"a correct predicate over an incomplete site enumeration."*

| # | Site | State |
| --- | --- | --- |
| **S-6** | **juniper-canopy `src/demo_mode.py:2019-2027` `_install_sequence_dataset`** | **THE ONE THAT BITES.** Reads `X_full` → falls back to `X_train`; same for `dt_full`, `y_full`. #589's patch has three hunks and does not touch it. Post-#369 no artifact carries `X_full`, so **every sequence install is train-only while the code claims whole-dataset** — `n_windows`, `lookback`, `n_features`, `windows_*` and histograms whose comment says "over ALL windows" all derive from it. Silent; nothing errors. |
| S-1 | juniper-data `storage/hf_store.py:145-146`, `storage/kaggle_store.py:242-243` | Two-way cut (`:107-109` / `:209-211`), write `*_full`, **no `X_val`**, and hardcode `generator_version="1.0.0"` (`:119` / `:218`) — never bumped, so R-1 is live there. **Zero callers outside the storage package and tests**, so library-only, not a service path. Whether these should partition at all is a product decision. |
| S-2 | juniper-ml `juniper-model-core/…/crossval/splits.py:6`, **published 0.3.1** | Docstring asserts D-CV-4's void premise ("folds are derived client-side from the `*_full` arrays"). Behaviour fixed by #150; the published text is not. |
| S-3 | juniper-data-client `docs/REFERENCE.md:639`, `:738`, `:746` | Say `NPZ_SPLITS=(…,"full")`; the constant is a 3-tuple. `:51` is already correct — internal drift. |
| S-4 | juniper-canopy `docs/demo/DEMO_MODE_REFERENCE.md:375` | "validates NPZ payload (`X_full`, `y_full`…)" — stale; code is right. |
| S-5a | juniper-recurrence **subdirectory** `juniper-recurrence/README.md:48` | `_full` in the crossval row. **The predecessor was right about this; the first draft wrongly refuted it — PREFLIGHT 2.** |
| S-5b | `juniper-recurrence-client/README.md:48` | Same line, same claim. |
| S-5c | `juniper-recurrence-client/juniper_recurrence_client/client.py:514` | **Published package docstring** — same class as S-2, not cosmetic. |
| S-7 | juniper-recurrence `juniper-recurrence/juniper_recurrence/main.py:53` | `--split` help reads `(train/test/full)` — advertises a dead value **and omits `val`**, while `schemas.py:83` is a bare `split: str` with no `Literal`, so `{"split":"full"}` is accepted. Predecessor's "inverse risk", now certain. |
| S-8 | juniper-data `generators/_sequence.py:232` **and `:325`** | Docstrings still assert ``X_full == concatenate([...])``. |

**Larger, gated:** `juniper-recurrence/bench/datasets.py` reads only `*_full`. Not a gate — but the
cap is **two lines, not one**: `juniper-recurrence/pyproject.toml:95` (`bench`) and **`:104`**
(`bench-equities`), both `juniper-data>=0.9.0,<0.12.0`. Widening only `:95` leaves the equities tier
pinned — the tier where §2's row-order exception actually lives.

---

## 4. The release train — merged everywhere, released nowhere

Measured 2026-09-07 (`gh api repos/O/R/compare/<tag>...main --jq .ahead_by`). **Decision 11 is in
ZERO published releases.**

| package | latest release | ahead | current version file | target | carries |
| --- | --- | --- | --- | --- | --- |
| juniper-data | `v0.13.0` (09-05) | **12** | `pyproject.toml` = `0.13.0` | **0.14.0** (breaking) | #369 |
| juniper-cascor | `v0.10.0` (08-30) | **25** | `pyproject.toml` = `0.10.0` | **0.11.0** (breaking) | #625 |
| juniper-data-client | `v0.4.2` (06-18) | **96** | `pyproject.toml` = `0.4.2` | **0.5.0** | #187, #190 |
| juniper-canopy | `v0.6.0` | **116** | — | — | #586, #589 |
| juniper-recurrence-model | `-model-v0.2.0` (07-29) | **52** | `_version.py` = `0.2.0` | **0.2.1/0.3.0** | **#150 — the crossval fix** |
| juniper-recurrence (app) | `-v0.4.0` (08-09) | **37** | `_version.py` = `0.4.0` | — | the crossval router |
| juniper-recurrence-client | `-client-v0.2.0` | **136** | `_version.py` = `0.2.0` | — | S-5c |
| juniper-ml (meta) | `v0.7.1` | **677** | — | — | #1761, #1805 |

**Traps in this table.**

- **Every repo still carries the version already on PyPI.** Cutting a Release without bumping
  re-publishes `0.13.0` / `0.10.0` / `0.4.2` and is rejected by the immutable TestPyPI upload — the
  juniper-ml#555 failure recorded in juniper-ml `AGENTS.md` § Publishing. **Bump first.**
- **juniper-recurrence is THREE packages with three trains** and three publish workflows
  (`publish-recurrence-{app,client,model}.yml`). Decision 11 splits across two of them — the model
  (`derive_full_split`) and the app (the crossval router). "`_version.py` reads 0.2.0" is ambiguous
  between the model and the client; both do.
- **`gh api releases/latest` sorts by semver, not date** — it returns
  `juniper-recurrence-model-v0.1.4` for this repo, which is **not** the newest release. Use
  `gh api repos/O/R/releases` and read `published_at`. juniper-data also carries pre-polyrepo
  `v0.2x.0-alpha` tags above `v0.13.0` in refname order, with no Release object.
- **Order — three phases, not four, and "publish" is dependency-ordered.** Plan `:165` says
  **"Client before producer … a consumer floor bump is unresolvable until the new CLIENT is on
  PyPI"**. `juniper-data-client` sits between `juniper-data` and *every* consumer (cascor
  `pyproject.toml:118`, canopy `:148`, recurrence `:52`), so "publish" is a sequence:
  **data-client → data → cascor / recurrence-model → canopy / recurrence-app → juniper-ml.**
  1. **Widen consumer ceilings.** Safe to do alone — a ceiling widen leaves the pinned resolution
     unchanged, so the Lockfile-Freshness sorted-pins diff is empty. First ceilings:
     `juniper-recurrence/juniper-recurrence/pyproject.toml:51-52`. juniper-ml's
     `pyproject.toml:67-69` (`<0.3.0` / `<0.5.0` / `<0.3.0`) **block** a model→0.3.0 or app→0.5.0 bump.
  2. **Publish**, in the order above.
  3. **Bump floors AND regenerate the lockfile IN THE SAME PR. Do not split them.** The gate runs
     `uv pip compile pyproject.toml --constraint requirements.lock`, so a merged `>=0.14.0` floor
     against a `==0.13.0` lock pin is *unsatisfiable* and **every subsequent PR in that repo goes
     red** until the regen lands. Incident: cascor#237 / canopy#250. The gate is in canopy, cascor,
     data **and juniper-cascor-worker**.
- **juniper-ml floors are `:30`, `:47`, `:48`, `:49`, `:67-69`** — `:49` is `juniper-data>=0.6.0`,
  **the producer half of the whole arc**. The first draft omitted it; bumping only cascor leaves
  `pip install juniper-ml[servers]` resolving a pre-`val` producer.
- **CHANGELOGs are not release-ready.** No `[Unreleased]` entry for the breaking change exists in
  juniper-data, juniper-cascor, juniper-canopy or juniper-recurrence-model. Worse,
  **juniper-data-client's `[Unreleased]` still asserts** *"`NPZ_SPLITS` becomes
  `("train","val","test","full")`; `"full"` is deliberately retained"* — falsified by its own #190 in
  the same unreleased window.
- **V-3 is an unmeasured behavioural change riding inside the cascor release.** Design `:386-388`:
  *"CLI early stopping changes CLI results … Measure it rather than assuming it is benign."* Plan
  `:186` homes it to Chunk 6; Chunk 6 shipped the plumbing and **nobody took the measurement**.
  Either measure before cutting 0.11.0, or say so in the release notes.

**Every deploy is a cut GitHub Release with notes archived under `notes/releases/` — never a bare
`git push <tag>`** (§11 of the PyPI publish procedure). **Paul approves every deploy and PyPI gate.**

---

## 5. Carried forward — risks, chunks, decision 12

The first draft dropped all of this. The plan is the rollout's **live register**; §9 of it is
current and §§2–7 are pre-review.

| item | plan says | verified today |
| --- | --- | --- |
| **R-1** | closed on the `val` bump | **re-opened and re-closed** for generators (all 16 at `3.0.0`), but **live in S-1**: hf/kaggle hardcode `generator_version="1.0.0"` |
| **R-2** | HIGH (`:210-217`) — consumers accept a changed contract silently | undisposed |
| **R-3** | HIGH | **remedied in code** — `juniper_data/core/models.py` has `n_val: int = 0` with a comment requiring it stay defaulted. The plan still rates it HIGH. |
| **R-9** | MEDIUM | undisposed |
| **S-5** (plan) | OPEN (`:27`) | undisposed |
| **S-7** (plan) | filed as **juniper-canopy#559** | **still OPEN**; its subject is live — `demo_mode.py:1904-1907` still justifies the rank probe with a claim #559 says is false in production |
| **Chunk 5** | data: §6.2 generate-shortfall + non-synthesisable exclusion | **not shipped**, and `:185`'s consequence column reads *"Chunk 8's option 0 has no backend"* — **Chunk 8 SHIPPED** (canopy#586). A shipped UI option with no backend. |
| **Chunk 7** | re-baseline (decision 4) + §7 snapshot provenance + `plots_cascor.py` + `snapshot_attribute.py` | **half shipped** — #1805 did the last two (`:155`). The **re-baseline and snapshot partition provenance are untouched**, and their consequence column reads *"Pre/post results silently comparable when they are not"* — across a `val` addition, a `*_full` removal and two `generator_version` bumps. |
| **Decision 12** | adopted 2026-09-03, schema *described not specified* | `partition_provenance` returns **zero hits** repo-wide in juniper-data, juniper-data-client and juniper-cascor (validated instrument: the same query shape returns 13/6/3 for known-present terms). No code has moved. |
| **Decision 5** | *"the CLI gains `eval` and early stopping"* (design `:371`) | **UNIMPLEMENTED.** `juniper-cascor/src/main.py` has zero `X_val`/`x_val`/`val_x`; the gate is service-only. Decision 12 is the only unimplemented member of the §9.2 **contract** set — it is not the only unimplemented decision. |
| **V-2 / V-3** | open in design §9.1 | undisposed; V-3 is decision 5's measurement and rides inside the cascor release (§4). |

---

## 6. Traps

**Merge / CI**

- **An unresolved CodeQL thread blocks a merge while every check reads green.** Fingerprint:
  `BLOCKED` + `MERGEABLE` + all required contexts green. `gh pr checks` cannot see it; query
  `reviewThreads(isResolved:false)`. Hit on cascor#625 (12 threads, unused locals from 3-tuple
  unpacks). **Fix the code — bind `_`.** A `# noqa` satisfies flake8, not CodeQL, and is worse than
  none.
- **Squash-merge ships only the FIRST commit's diff** when a later commit corrects an earlier one.
  #369 was collapsed with `git reset --soft origin/main` before force-pushing for exactly this.
- **A force-push does not reliably fire `synchronize`.** Confirm with
  `gh api "/repos/O/R/actions/runs?head_sha=<FULL sha>" --jq .total_count` — **a short SHA returns 0
  and looks like a failure to trigger.** Repair: `gh api -X PUT /repos/O/R/pulls/N/update-branch`.
- **`gh` 2.46.0 breaks ALL `gh pr edit`** — patch bodies via
  `gh api -X PATCH repos/O/R/pulls/N -F body=@file`.
- **`util/safe_merge.py` wants a bare repo name; `util/ad-hoc/2026-09-05_auto_merge_shepherd.py`
  wants `owner/repo`**, reports `NOT-ARMED` transiently from GraphQL, and background waiters get
  OOM-killed — never run two on one PR.
- **Sequence-safety needs CI's scope** (`--scope 'juniper_data/**'`, `'src/**/*.py'`); a bare
  invocation reports `files_screened=0` and is vacuous. **`Allow-Symbol-Loss:` is NOT a git
  trailer.** `juniper_ci_tools/symbol_loss_check.py:171` reads `git log --format=%B base..head` and
  `:418` matches `^\s*Allow-Symbol-Loss:` with `re.MULTILINE` — so it matches **at any indentation,
  in any commit in the range, anywhere in the body**, including a quoted diff or a pasted CI log.
  Keep the token out of quoted text. The value is token-split on `[,\s]+` (`:427`), so **no prose**
  on that line — a reason is parsed as symbol names. (The "last paragraph" rule is real but belongs
  to *git's* trailer parser, `%(trailers:key=X)` — a different mechanism this tool never consults.)

**Release-specific**

- **`juniper-cascor-model/` drift guard**: edits to `src/{candidate_unit,utils,log_config,cascor_constants}`
  must be mirrored byte-for-byte; `test_drift.py` catches it only in CI. A release-prep edit trips it.
- **cascor's `src/tests/integration/` is marker-gated** — skips without `--integration`, so a
  pre-release verification run reads green having skipped the tier.
- **`tests/test_env_repr_safety.py`** forbids `dict(os.environ)` and scans source **text**, so it
  fires on comments.
- **juniper-ml's `ci.yml` test list is hand-maintained** — a new test *file* does not self-register.
- **AGENTS.md edits require today's UTC date** where `agents-md-touch-up.yml` runs (juniper-data,
  juniper-ml); juniper-ml also gates AGENTS.md size — `python3 util/memory_budget_check.py`.

**Search / shell**

- **A sweep reuses its own pattern.** Three sweeps this session missed sites: `head -40` truncated a
  census; `_, _, _ = result` did not match a `(x_full, y_full)` pattern; `return_value=` was
  explicitly *filtered out* and hid three stubs. Grep the concept; prove the enumeration.
- **`sed` with a broad pattern hits every match** — a mutation check here rewrote eight `continue`
  blocks. Revert with `git checkout --` and re-apply precisely.
- **This worktree-isolated session refuses** heredocs, `cd` to the shared checkout, bare globs where
  an option could stand, `awk` programs, and compound commands naming git with runtime values.

---

## 7. Verify the starting state

Every negative check below is paired with a **positive control**, because
`gh api … | base64 -d | grep -c X` returns **0 for a 404, a typo, a moved file or an expired token**
— indistinguishable from "the thing is gone".

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-tumbling-puppy
set -o pipefail
git status --short && git log --oneline -1
gh pr view 1808 --repo pcalnon/juniper-ml --json state,mergeStateStatus,autoMergeRequest

# Producer really stopped. NEGATIVE expects 0; POSITIVE must return 1 or the read failed.
gh api repos/pcalnon/juniper-data/contents/juniper_data/core/split.py -q '.content' \
  | base64 -d | grep -c 'split\["X_full"\] = '        # expect 0
gh api repos/pcalnon/juniper-data/contents/juniper_data/core/split.py -q '.content' \
  | base64 -d | grep -c 'split\[name\] = array\[:total\]'   # expect 1  <-- proves the file was read

# PREFLIGHT 2 -- the ambiguity. Root = 0, SUBDIRECTORY = 1. Both must hold.
gh api repos/pcalnon/juniper-recurrence/contents/README.md -q '.content' | base64 -d | grep -c '_full'
gh api repos/pcalnon/juniper-recurrence/contents/juniper-recurrence/README.md -q '.content' \
  | base64 -d | grep -c '_full'

# PREFLIGHT 1 -- the release gap that keeps crossval broken.
gh api repos/pcalnon/juniper-recurrence/releases --jq '.[] | select(.tag_name|test("model")) | "\(.tag_name) \(.published_at)"' | head -2
gh api repos/pcalnon/juniper-recurrence/contents/juniper-recurrence/pyproject.toml -q '.content' \
  | base64 -d | sed -n '51,52p'

# S-6, the silent one. Expect BOTH X_full and the X_train fallback -- if either is missing, re-read.
gh api repos/pcalnon/juniper-canopy/contents/src/demo_mode.py -q '.content' \
  | base64 -d | sed -n '2019,2027p'

# §4 -- versions still equal what is published.
gh api repos/pcalnon/juniper-data/contents/pyproject.toml -q '.content' | base64 -d | grep -m1 '^version'
gh api repos/pcalnon/juniper-data/compare/v0.13.0...main --jq '.ahead_by'

# §3 -- the census. Run the instrument, do not hand-roll a grep.
python3 util/ad-hoc/2026-09-05_census_full_family_v2.py | head -14

# §5 -- decision 12. Instrument sanity first: the control MUST be non-zero.
gh api 'search/code?q=partition_and_assemble+repo:pcalnon/juniper-data' --jq '.total_count'  # >0
gh api 'search/code?q=partition_provenance+repo:pcalnon/juniper-data' --jq '.total_count'    # 0
```

---

## 8. Git status at handoff

Branch `docs/decision-11-shipped` (juniper-ml#1808), pushed, auto-merge armed, regression tests
pending. juniper-ml#1807 **MERGED** 14:28:23Z. Working tree carries this file.

**The parent `/home/pcalnon/Development/python/Juniper/AGENTS.md` was edited this session** — data
contract rewritten for decision 11, juniper-recurrence added to Active Repositories, conda table
corrected to `JuniperCascor1`/`JuniperCanopy1` with real Python versions. **It is in no git
repository**: no PR, no CI, no history, and **invisible to every other machine**. juniper-ml#1807
records why it cannot even be linked.

**Worktrees.** Three created this session (cascor, recurrence, juniper-data) were removed and pruned
after confirming their only ignored content was build caches. Three remain from earlier sessions and
were left alone — another session may hold them:

```
worktrees/juniper-canopy--feature--drop-full-family--20260905-1300--c2c3cb7f
worktrees/juniper-data--feature--drop-full-family--20260905-1330--cc15640c
worktrees/juniper-data-client--feature--drop-full-family--20260905-1215--7d5b2f60
```

`git worktree remove` **deletes ignored files**, which `git status --porcelain` alone will not show —
use `--ignored`.

---

## 9. What this evidence cannot support

- **No tests were run in this validation.** Every claim comes from source, git, the GitHub API and
  PyPI — **not from a green run**. §1's "landed" and "CLOSED" are static verifications.
- **The sequence tier's `t_*` / `dt_*` / `observed_mask_*` families were not inspected for `_full`
  members** (design §9.5.5 bullet 3, still open). §1's producer check greps `split["X_full"]` in
  `core/split.py` and would not see a `dt_full` written elsewhere — and S-6 is exactly a `dt_full`
  read.
- **Whether S-1's stores should partition at all** is a product decision, not a measurement.
- **Row-order sensitivity of the ~180 migrated juniper-data assertions** is unaudited; **21
  juniper-data test files still reference `X_full`**, so removing the store writes needs them checked.
- **Whether the three inherited worktrees are idle** — inferred from merged PRs, not probed.
- **Whether canopy's `*_train` fallback (S-6) was deliberate compatibility or an omission** — #589's
  body and patch say neither.
- **Anything outside the 11 scopes** the census covers.

---

## 10. Consensus record (§7 minimum record)

**Instrument.** Direct re-derivation from primary artifacts: `gh api repos/O/R/contents/<path>`
against `origin/main`; `gh api .../compare/<tag>...main` for release distances;
`gh api search/code` with a **validated control** for absence claims; and the committed census
`util/ad-hoc/2026-09-05_census_full_family_v2.py`. **Could it have produced a different answer?**
Yes — it produced a different answer **eleven times** (§11).

**Sizing (§3 of the procedure).** High criticality (document of record; gates a release train),
medium uncertainty. Escalators: overturns standing claims in `docs/REFERENCE.md` and in the
predecessor; contains universal quantifiers ("nothing emits", "released nowhere").

**Pool.** 5 agents, 1 round, ~220 tool calls. **Lane A ×3, genuinely different entry points** —
A1 git/PR/release history only (forbidden the design docs); A2 source-as-it-stands only (forbidden
PR bodies and commit messages); A3 claim-tracing against a fixed list, returning
AGREE/DISAGREE/UNTRACEABLE. **Lane B ×2, briefed to REFUTE** — B1 correctness lens; B2
omission/amputation lens against the predecessor.

**Reconciliation.** Every load-bearing finding was **re-derived by the orchestrator before being
written here** (§5.2). That mattered: it confirmed all eleven corrections and the four
independent-convergence items below.

**Convergence across independent entry points** (the thing that makes agreement meaningful): the
canopy `_install_sequence_dataset` train-only fallback was found by **A1 and B2 separately**; the
dual bench cap by **A3 and B2**; the `manager.py:3649` non-overridability by **A2 and A3**.

**Sample size.** 11 census scopes; 9 repositories; 7 merged PRs; 8 release trains; 15 traced claims.

**Dissent, and how it was settled.** Two measurement disputes, both settled by opening the artifact
(§5.1) rather than by majority:

1. **`juniper-recurrence/README.md` — A3 vs. B1 *and* the first draft.** A3 said the subdirectory
   README has `_full`; B1 and the draft said it does not. **A3 is right**, and the other two fell
   into the *same* ambiguity independently: `gh api …/contents/README.md` → 0 hits;
   `gh api …/contents/juniper-recurrence/README.md` → 1 hit at `:48`. Two of five agents plus the
   author making the identical path error is itself the evidence that PREFLIGHT 2 is worth its space.
2. **`manager.py` line numbers — B1 vs. A2/A3.** B1 reported `:3649` as a blank line. It is not:
   counting from `:3645`, the rule-3 `raise` is at **`:3649`**, the rule-2 `raise` at **`:3657`**,
   its message string at `:3658`. **B1 wrong, A3 right on `:3657`.** B1's substantive point — that
   the override attaches to only one of the two rules — is correct and is now stated in PREFLIGHT 3.

**Findings NOT adopted**: B1's defect 6 (a "false parenthetical" about `-v0.1.4`) duplicates the
draft's own correction #4; B1's defect 16 (release direction "inverted") was a wording fix, applied.

**Convergence worth trusting**: S-6 (canopy sequence path) was found **independently by A1, B2 and
B1** from three different entry points. The dual bench cap by A3 and B2. `:3649`'s
non-overridability by A2 and A3.

---

## 11. What the review overturned

Four of these are errors **this document's own first draft** introduced — which is what §4 of the
consensus procedure predicts ("the fix pass is the least trustworthy part of any document").

| # | claim in draft 1 | verdict |
| --- | --- | --- |
| 1 | *"`juniper-recurrence/README.md` does NOT mention `_full` — the predecessor's claim is refuted"* | **WRONG, and it wrongly discredited the predecessor.** The path is ambiguous; the draft greped the repo root, the predecessor meant the subdirectory. Two further sites went with it, one a **published docstring**. |
| 2 | `manager.py:3649` and `:3658` both overridable | **WRONG.** `:3649` (rule 3) is not overridable; the overridable raise is `:3657`. |
| 3 | Release table of three repos | **INCOMPLETE.** Eight trains across six repos; data-client (96 ahead) is the predecessor's named *blocker*; juniper-recurrence is three packages. |
| 4 | *"latest release object is `-v0.1.4`"* | **FALSE** — an artefact of `releases/latest` sorting by semver, not date. |
| 5 | juniper-ml floors `:30, :48, :67-69` | **INCOMPLETE** — omitted `:47` and **`:49` (`juniper-data>=0.6.0`)**, the producer half. |
| 6 | (absent) | **S-6**: canopy renders sequence datasets **train-only** post-#369, silently. Highest-cost finding. |
| 7 | (absent) | canopy is the **second** consumer of the row-order asymmetry and has **no** reordering. |
| 8 | (absent) | Every repo still carries its **published** version — cutting a Release without bumping fails (juniper-ml#555 class). |
| 9 | (absent) | R-2/R-3/R-9/S-5/S-7 and Chunks 5/7 dropped entirely; **canopy#559 is still OPEN**; Chunk 8 shipped with no Chunk-5 backend. |
| 10 | (absent) | §7's checks **fail open** — 0 on a 404. Positive controls added. |
| 11 | (absent) | Dropped traps restored, including the **entire environment block** (deprecated conda envs) and "status transcribed is not status". |
| 12 | §2: *"Nothing emits it"* | **FALSE and self-contradicting** — §3's S-1 says hf/kaggle still do. Worse, §2's remedy (three-way concat) **raises `KeyError`** on those artifacts, which carry no `X_val`. |
| 13 | §2: *"same rows, different permutation"* | **FALSE for tabular `equities`.** `generator.py:335` appends the **entire frame** as `full` while partitions are ratio-bounded slices, and `params.py:143` permits ratio sums **below** 1.0 — so legacy `X_full` is a strict **SUPERSET** and reconstruction is **lossy**. No reordering recovers rows in no partition. |
| 14 | §4: "publish" as one step | Plan `:165` says **"client before producer"** — `juniper-data-client` publishes FIRST. The draft paraphrased "client" as "package", erasing the ordering constraint §5 of the plan exists to state. |
| 15 | §4: "bump floors → regenerate lockfiles" as two phases | **Splitting them reddens the repo.** The gate compiles against the lock, so a merged floor with a stale pin is unsatisfiable and every later PR fails (cascor#237 / canopy#250). Same PR, always. |
| 16 | §1: "six PRs, 2026-09-06" | **Eight PRs, 09-05 → 09-06** — four merged on the 5th. A date-filtered log loses half the arc. |
| 17 | §1: "decision 12 is the only unimplemented decision" | **Decision 5 is too** — cascor's CLI has zero `X_val`. 12 is the only unimplemented member of the *contract* set. |
| 18 | §6: `Allow-Symbol-Loss` "must be the final trailer paragraph" | **FALSE** — it is a `re.MULTILINE` match over raw commit bodies, position-independent. The draft generalised git's trailer rule onto a tool that never consults it. |
| 19 | header vs §0.3 | The parent `AGENTS.md` was listed as CHANGED while still carrying the unqualified "cascor refuses". **Fixed this round**, in the file itself. |

**Round 2 was not run as a separate pool.** Corrections 12–19 came from Lane B and were each
re-derived by the orchestrator, but **the fix pass applying them is itself unreviewed** — which is
exactly the risk §4 of the consensus procedure names. A successor treating §2, §3, §4 or §5 as
authoritative should re-derive with §7's commands first; they are written so a failed read cannot
read as a pass.
