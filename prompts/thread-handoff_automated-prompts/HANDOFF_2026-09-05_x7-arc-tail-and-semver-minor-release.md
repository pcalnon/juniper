# HANDOFF 2026-09-05 — X7 arc tail: the SemVer correction, and what is left

**Session**: X7 event-loop blocking — slices 1c + 1d, then PRs 2/3/4
**Predecessor**: <https://claude.ai/code/session_01UmoPmGT78dzGKFDCewdHFZ>
**Status of the arc**: **X7 is closed.** Constraints C1–C10 are all addressed and merged.
What remains is a release-versioning correction plus two follow-ons that depend on it.

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **X7 arc tail**. The remediation itself is done and merged; the outstanding
work is a **release-versioning correction the owner has decided**, its two dependants, and
one deferred item.

### The decision that drives this handoff

**`juniper-cascor-client` must be released as `0.8.0`, not `0.7.1`.** The owner has ruled
that SemVer practice governs: the release adds `backoff_factor` as a **new public
constructor parameter** (`APD-CCLIENT-013`), which is an additive **feature**, and a
feature is a MINOR bump. The merged `0.7.1` understated it as a patch.

`0.7.1` was chosen for a downstream reason, not a semantic one: **juniper-canopy caps that
dependency at `<0.8.0`**, so a `0.8.0` release would be excluded by the very consumer the
release exists to serve. That cap is now the thing to change, not the version.

**This is a two-part change and both parts must land before the Release is cut**, or
canopy cannot install the artefact:

1. **juniper-cascor-client** — bump `0.7.1` → `0.8.0`.
2. **juniper-canopy** — widen the cap so `0.8.0` is admissible.

### Remaining work

1. **Bump juniper-cascor-client to 0.8.0.** Four carriers, all of which the merged 0.7.1
   change touched — `pyproject.toml`, `juniper_cascor_client/__init__.py:__version__`,
   `juniper_cascor_client/constants.py` header, and **`AGENTS.md`**. The last one is not
   optional: a CI step named *"Lint AGENTS.md version vs pyproject.toml"* fails the
   **Documentation Links** check on drift, and it caught exactly that omission last
   session. Rename `notes/releases/RELEASE_NOTES_v0.7.1.md` → `_v0.8.0.md`, retitle it
   MINOR, and delete its "Versioning note" section — that section exists only to flag the
   tension this bump resolves. Re-head `CHANGELOG.md`'s `[0.7.1] - 2026-09-05` as
   `[0.8.0]`.
2. **Widen canopy's cap.** Verified: it is a **single line** —
   `juniper-canopy/pyproject.toml:162`, `"juniper-cascor-client>=0.7.0,<0.8.0"`. The three
   `requirements*.txt` files mention the package only in a comment, so nothing else needs
   editing. Widen the ceiling to admit `0.8.0` (e.g. `<0.9.0`). **Do not raise the floor to
   `>=0.8.0` yet** — see step 4; canopy cannot install a version that is not published.
3. **Owner cuts the GitHub Release.** *Not an agent action.* The repo's own
   `notes/releases/RELEASE_NOTES_v0.7.0.md` says "the owner cuts the GitHub Release", and
   the ecosystem convention routes it through `publish.yml`
   (`juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11).
   Ask; do not tag or publish.
4. **After it is on PyPI**, pin canopy's floor to `>=0.8.0` and re-run canopy's suite
   against the published wheel rather than the local checkout. PyPI's CDN lags ~5–30 s;
   query the version-specific endpoint, not the index.
5. **juniper-canopy#582 (PR 2, demo-mode honesty)** — auto-merge armed, currently `BEHIND`.
   It should land on its own; if it stalls, `util/safe_merge.py --pr 582 --repo
   juniper-canopy --execute` refreshes the base and re-arms.
6. **Deferred, named in juniper-deploy PR 3 and not done**: `image: juniper-canopy:latest`
   wants a pinned release tag. It needs a published image and a release decision, not a
   guess.

### Why the release matters — this is not bookkeeping

PyPI's `0.7.0` retries on `["GET","POST","DELETE","PUT","PATCH"]`. `main` has carried
`["HEAD","GET"]` since `ff3df6c`, unpublished, because `pyproject.toml` never left `0.7.0`.
That is **constraint C8** — *"retries must not be applied to non-idempotent verbs"* —
measured as **`POST /v1/training/start` reaching cascor 4×**. A retried training-start is
not a slow request; it is up to four training runs. Every consumer installing from PyPI
still has that defect until this ships.

### Completed and merged this session

| Change | Repo | Commit |
| --- | --- | --- |
| Slice 1c — status cache + classifier | canopy | `644967b` (#578) |
| Slice 1d — admission control (**C4 + C10**) | canopy | `c2c3cb7` (#581) |
| PR 3 — alerts + liveness probe | juniper-deploy | `8bf0925` (#206) |
| PR 4 — release 0.7.1 (**to be superseded by 0.8.0**) | cascor-client | `4b401ac` (#154) |
| PR 2 — demo-mode honesty | canopy | #582, auto-merge armed |

Earlier in the arc: 1b (`ee2ec79`, #566), 1a (`94220f0`, #567) — **1a is what closes X7** —
plus juniper-ml `42d33634` (#1661) and `d69c9a73` (#1636) correcting the design and its
operator surface to the real count of **58** sites.

### Key context — settled; do not re-litigate

- **The gate's authority is scoped to `main.py`.** Four of the 58 sites live outside it.
  `juniper-canopy/util/ad-hoc/2026-09-04_async_blocking_callgraph.py` is the instrument for
  the rest — **run it when touching the adapter**. It has a known blind spot: `getattr`
  dispatch (`getattr(adapter, "list_snapshots")`), which is how two real sites hid from it.
- **`offload` is an offloader.** Slice 1d's wrapper is in the 1a gate's `OFFLOADERS`, matched
  as a Name call as well as an Attribute one. Removing it makes the gate fail *because the
  code got safer*.
- **C5 was refuted on inspection, and the refutation is narrower than "wrong".** Its premise
  held; its *remedy* did not. `JuniperCascorClient` mutates session state only in
  `__init__`, so the shared object is a thread-safe urllib3 pool. C5 is restated as the
  invariant T-A4 pins: **no per-request session mutation**.
- **`INDETERMINATE` must never page.** An open breaker means the call was *skipped*, so the
  tick observed nothing; alerting on it claims evidence never gathered.
- **Demo-mode honesty gates probe tightening.** Tightening liveness before demo mode is
  honest converts a loud, self-recovering hang into a fast, silent restart *into the
  simulator*. PR 2 is that gate; PR 3 was sequenced after it.

### Traps that cost this session time

- **`grep … | head -20` truncated a finding into a false one.** I concluded canopy's metrics
  were "documented, configured and unreachable" from output cut off before lines 693/704.
  They were correctly wired all along; the real gap was one dev-only service. **Count the
  matches before believing an absence.**
- **Tests can pin the defect.** Two canopy integration tests asserted `size_bytes > 0` for
  every snapshot under the *demo* fixture — i.e. they required the fabricated size PR 2
  removes. A failing test is not automatically a regression.
- **A green rollup next to `BLOCKED` is a review thread, not a check.** Canopy requires
  review-thread resolution; CodeQL opens threads that do not always auto-resolve. Verify the
  alert is actually closed (`code-scanning/alerts?ref=…&state=open`) before resolving one.
- **`safe_merge` arms an auto-merge net before it waits.** A client-side timeout does not
  abort the merge; check `autoMergeRequest` before re-running.
- **A typed helper surfaces latent type errors.** 1d's generic `offload` made mypy see
  through `to_thread`'s `Any` and flag a real undeclared TypedDict key at `main.py:4085`.

### Verification commands

```bash
# cascor-client: the divergence the release exists to close
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
git show v0.7.0:juniper_cascor_client/constants.py | grep RETRY_ALLOWED_METHODS   # 5 verbs
grep RETRY_ALLOWED_METHODS juniper_cascor_client/constants.py                     # HEAD, GET

# cascor-client suite — use JuniperCascor1; JuniperCanopy1 lacks the `responses` test dep
/opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest tests/ -q -p no:randomly

# canopy full suite (~6100 tests)
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda run -n JuniperCanopy1 python -m pytest tests/unit/ tests/regression/ -q -p no:randomly
```

### Git state

All work is committed, pushed and merged except canopy#582 (auto-merge armed, `BEHIND`).
No session worktrees remain for 1a/1b/1c; the 1d, PR 2, PR 3 and PR 4 worktrees are still
present under `Juniper/worktrees/` and are **safe to remove once #582 lands** — check
ignored files first (`git status --short --ignored`), since `worktree remove` deletes them
silently and porcelain is blind to them.

---
