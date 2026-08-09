# HANDOFF 2026-08-09 — release-train shipping round: outstanding work + open questions

Continue the Juniper PyPI shipping arc and its follow-ups. Standing policy: headless merges only on Paul's explicit per-PR/group approval; guardrails (checks RAN+green, no union resolutions, defective PRs get corrected re-lands) always apply.

## Completed (this arc)

- **On PyPI**: juniper-ci-tools 0.8.0, juniper-model-core 0.3.1, juniper-service-core 0.5.1, juniper-ml 0.7.1, juniper-recurrence 0.4.0 (all Gate-2-approved by Paul).
- ml#1029 `Allow-Archive-Edit:` trailer escape merged (archive guard is a required check; modify-in-`notes/releases/` PRs green via trailer + owner approval; carry trailer into squash). Closed #1013.
- ml#1038 two-phase TestPyPI verify merged + **live-proven** on v0.7.1 (download `--no-deps` from TestPyPI → install wheel[extra] from PyPI only; kills the TestPyPI-squatter dependency-confusion class, e.g. fastapi 1.0).
- ml#1040: v0.7.0 → **0.7.1** bump — v0.7.0's tag name was permanently retired by **release immutability** after its failed publish (never delete-and-recut; always bump).
- ml#1015 AGENTS.md version-table co-change live-proven (recurrence#103 carried header + table row). cascor#498 protocol CHANGELOG bullets (Fixed+Changed → 0.2.0). cascor#499 proposal merged incl. version-test heal (form + pyproject-lockstep assertions). cascor#488 weights-reject requeue merged.

## Remaining work (in order)

1. **cascor main is RED** at Paul's own push `4d07a88` (2026-08-09 08:16): CI/CD + WS-6 Golden Regression + main-verify failing. His push — diagnose/heal only with his go, or he fixes.
2. When cascor main greens: scoped ceremony `gh workflow run release-train.yml -f mode=ceremony -f packages="juniper-cascor, juniper-cascor-protocol"` → cascor 0.8.0 + protocol 0.2.0 → Paul's Gate 2. Keep ceremonies SMALL: 4 ceremony runs were cancelled mid-monitor (canceller unknown — API hides it; check the Actions UI on runs 31281804290/31283688714/31301879756/31304571130). Cuts are durable; monitors are observation-only.
3. After protocol 0.2.0 is on PyPI: bump cascor's `juniper-cascor-protocol` floor to `>=0.2.0` and **remove the #463 shim** (`src/api/workers/protocol.py` BinaryFrame subclass → passthrough); note the deeper trap: cascor's unit lane tests the *published* wheel, not in-repo protocol source.
4. service-core's storm batch (coordinator requeue cluster etc.) still in `[Unreleased]` → future propose round (likely 0.6.0; ml `[tools]` ceiling `<0.6.0` will need the RK-11 co-change — propose handles it).
5. Open owner decisions: ml#1011 (Sequence-Safety required promotion — standing-items memory says soak-hold ~08-21), ml#1012 (bypass-actor removals).
6. Optional follow-ups: cascor test-suite audit for under-modeled bare-`object()` stubs (the #472 class); local ceremony runs blocked by a tag-creation restriction local tokens don't bypass (Actions path works — low priority mystery).

## Key context

- Release-train lessons (immutability / two-phase verify / cancellation mitigation) recorded in memory topic `project_pypi_release_train_plan_2026-07-11`; storm playbook in `project_juniper_ml_concurrent_session_activity`.
- Concurrent sessions own: sequence-safety rollout (8/8 complete), CLI experimentation Waves 3.x, canopy E2E arc. Dup-guard (`gh pr list`) before touching anything.
- Proposal PRs branch as `release/<pkg>-vX.Y.Z`; recurrence proposals need no hand-heal since ml#1015.

## Verify starting state

```bash
gh run list --repo pcalnon/juniper-cascor --branch main --limit 3   # red until healed
gh release list --repo pcalnon/juniper-ml --limit 3                  # v0.7.1 top
pip index versions juniper-ml                                        # 0.7.1 once CDN settles
gh pr list --repo pcalnon/juniper-ml --state open                    # expect ~0 session PRs
gh issue list --repo pcalnon/juniper-ml --state open                 # 1011/1012 + backlog
```

Git: session worked from worktree `compiled-crunching-river` (detached/branches; never holds `main`). No uncommitted session work pending after this handoff merges.
