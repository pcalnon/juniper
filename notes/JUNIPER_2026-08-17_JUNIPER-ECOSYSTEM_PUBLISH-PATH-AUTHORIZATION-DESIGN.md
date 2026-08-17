# Publish-Path Authorization — Design and Analysis

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (all 9 repos)
**Author**: Paul Calnon
**Status**: **APPLIED 2026-08-17** — owner decisions D1–D4 answered; P1 + P2 rolled out fleet-wide
and proven by a negative and a positive control (§12). P3 / P4 remain planned.
**Date**: 2026-08-17
**Supersedes**: nothing. **Closes analysis for**: juniper-ml#357, juniper-ml#358, and the
"TestPyPI gap" raised in the 2026-08-15 ruleset register.

---

## 1. Decision requested

The publish path is **authenticated** (OIDC trusted publishing, short-lived tokens) but only
**partially authorized**: nothing structurally constrains *which ref* may deploy to either package
index, on any repo. This document proposes closing that with GitHub **environment deployment
tag policies** plus **PyPI-side environment binding**, while preserving hands-free automated
TestPyPI deployment from a credentialed agentic session.

Four owner decisions are listed in §9. Nothing here has been applied.

---

## 2. Current state (probed live 2026-08-16 / 2026-08-17)

### 2.1 Environment protection, all 9 repos

> **Superseded by §12** — this section records the state that motivated the design. All 16 publish
> environments were remediated on 2026-08-17; juniper-deploy's two were deleted.

| Repo | `pypi` env | `testpypi` env |
|---|---|---|
| all 8 publishing repos | `reviewers(pcalnon)` + `wait(5m)`, **refs: ANY** | **no rules**, **refs: ANY** |
| juniper-deploy | **no rules**, refs: ANY | **no rules**, refs: ANY |

Every environment on every repo has `deployment_branch_policy: null` — i.e. **any ref may deploy
to any environment**. This is the core finding, and it is wider than the original "TestPyPI gap":
the `pypi` environment is equally unrestricted, with a human reviewer as the sole control.

juniper-deploy carries `pypi` / `testpypi` environments with **no protection at all** despite
publishing no package (§9 D4).

### 2.2 Workflow-level guards

`publish.yml:46` (meta) and `publish-<pkg>.yml:54` (six siblings) gate the build job on the
release tag prefix — but both **exempt `workflow_dispatch`**:

```yaml
# meta
if: github.event_name == 'workflow_dispatch' || startsWith(github.event.release.tag_name, 'v')
# siblings
if: github.event_name != 'release' || startsWith(github.event.release.tag_name, 'juniper-ci-tools-v')
```

This is deliberate and documented (`publish.yml:28-31`) as an operator escape hatch for re-firing
a failed publish. It is also precisely the hole #357/#358 described.

**No tag ↔ version consistency check exists** in any publisher. Both read the version from
`pyproject.toml`, but only to construct the *verify-install* command — never to assert it matches
the triggering tag.

`id-token: write` is declared at **workflow** level in every publisher, not scoped to the publish
jobs (#357's third ask, unaddressed).

### 2.3 What actually runs today

Empirically, every publish run on ml and cascor is `event=release` with the ref being the **tag**:

```
2026-08-09  event=release  ref=v0.7.1                       success
2026-08-09  event=release  ref=juniper-service-core-v0.5.1  skipped
2026-08-14  event=release  ref=v0.9.0                       success   (cascor)
2026-08-10  event=release  ref=juniper-cascor-protocol-v0.2.0 skipped
```

**No production publish has ever run from a branch.** This is what makes the proposed control
non-breaking: a tag policy would have admitted every historical run unchanged.

---

## 3. Threat model

**Principal**: any identity that can commit to the repo or dispatch a workflow — which now
explicitly includes *agentic sessions* holding repo write, plus the release-train GitHub App.

**Capability today**:

1. Dispatch `publish.yml` with `--ref <any branch>`; the `workflow_dispatch` exemption skips the
   tag guard, the build job builds that branch, and the artifact flows downstream.
2. `testpypi` has no protection rules → **publishes with no gate whatsoever**.
3. `pypi` requires one approval. The approval UI shows the ref, but this is a human check against a
   familiar-looking run, not a structural one — the same class of control that the March 2026
   litellm compromise defeated by uploading outside the normal release process.
4. Alternatively: modify the workflow itself. PyPI's own security model names this directly —
   *"anybody who can unconditionally commit to your repository can also modify your publishing
   workflow to make it trigger on events you may not intend (e.g., a manual `workflow_dispatch`
   trigger)."*

**Blast radius of (2)** is larger than "it's only TestPyPI":

- TestPyPI is a public index serving the real `juniper-*` names; anything published there is
  installable by anyone who adds it as an index.
- The meta `publish.yml` **Gate 1 verify installs *from TestPyPI*** (bare → `[clients]` → `[tools]`).
  TestPyPI is therefore an input to our own release gate, not just a rehearsal target.

**Not in scope**: token exfiltration. Trusted publishing already bounds that — the credential is
short-lived (≤15 min) and minted per run, which is why the residual risk is entirely about *who
may invoke the publisher*, not about stealing a long-lived token.

---

## 4. Best practices identified

| # | Practice | Adopted? |
|---|---|---|
| B1 | Trusted publishing via OIDC; no long-lived API tokens | **Yes** |
| B2 | Dedicated environment per index | **Yes** (`pypi`, `testpypi`) |
| B3 | Required reviewers on the production environment | **Yes** (`pypi` only) |
| B4 | **Deployment branch/tag policies restricting which refs may deploy** | **No — the gap** |
| B5 | **PyPI-side trusted publisher bound to the environment name** | **Unknown — §5** |
| B6 | Treat a Trusted Publisher as an API token: if code shouldn't reach the token, it shouldn't reach the publisher | partial |
| B7 | Scope `id-token: write` to the publishing job only | **No** |
| B8 | Review Trusted Publishers on maintainer offboarding (they attach to the *project*, not the user) | n/a (solo) |

B4 is the control that matches this threat model. GitHub evaluates environment protection rules
**before the job starts** and independently of the trigger — *"the job won't start until all of the
environment's protection rules pass"* — so a tag policy blocks a `workflow_dispatch` from a branch
without needing the workflow's own `if:` to be trustworthy. That property is what makes it a
control rather than defense-in-depth: it survives an attacker who edits the workflow.

---

## 5. The load-bearing unknown — PyPI-side environment binding

**PyPI verifies the OIDC `environment` claim only if the trusted publisher is configured with an
environment name.** If the field is blank on PyPI's side, a token carrying *any* environment claim
— or none — is accepted.

Consequence: if our publishers were registered without the environment name, then **every
environment gate described above is decorative from PyPI's perspective**. A workflow that simply
omits `environment: pypi` would publish with no reviewer, no wait timer, and (after this design)
no tag policy.

This was tracked as pypi/warehouse#17241 and closed with a warning/error path (PR #17281),
explicitly motivated by the Ultralytics supply-chain attack. The remedy is one-line: ensure each
project's Trusted Publisher names the environment.

**I cannot verify this** — it requires the PyPI / TestPyPI project settings, which are owner-only.
It is decision **D1** and it gates the value of everything else in this document.

---

## 6. Design options

### Option A — Environment tag policies (**recommended**)

Restrict each publishing environment to the release tag patterns that legitimately deploy.

```bash
# 1. switch the environment to custom ref policies
gh api -X PUT repos/pcalnon/<repo>/environments/<env> \
  -f 'deployment_branch_policy[protected_branches]=false' \
  -f 'deployment_branch_policy[custom_branch_policies]=true'

# 2. add tag patterns (type=tag; wildcards do not match "/")
gh api -X POST repos/pcalnon/<repo>/environments/<env>/deployment-branch-policies \
  -f name='v*' -f type=tag
gh api -X POST repos/pcalnon/<repo>/environments/<env>/deployment-branch-policies \
  -f name='juniper-*-v*' -f type=tag
```

Two patterns cover the whole fleet: `v*` (meta / app releases) and `juniper-*-v*` (sub-packages).

**Effect**: a dispatch from a branch reaches the build job, then **fails at the environment gate**
before any credential is minted. A dispatch from a tag — the documented operator recovery, already
written into `publish.yml:31` as `gh workflow run publish.yml --ref <tag>` — still works.

**Preserves the automation requirement.** The release-train ceremony cuts a GitHub Release; that
creates the tag; the publisher fires `release: published` on the tag ref; the tag policy admits it;
TestPyPI publishes **with no human in the loop**; PyPI still waits at Gate 2. Nothing about the
agentic path changes.

| Pros | Cons / constraints |
|---|---|
| Structural — survives workflow edits | Per-repo × per-env config (18 environments); no ruleset-style fleet template |
| Non-breaking (§2.3: all historical runs pass) | Tag patterns must be kept in sync if a new tag convention appears |
| No new human gate; automation preserved | Blocks a *branch* dispatch even for legitimate debugging — intended, but a workflow change |
| Uses a first-class GitHub feature, no custom code | Does nothing if D1 (PyPI binding) is unset — see §5 |

### Option B — In-workflow ref + version assertion

A step asserting `github.ref` matches the expected tag pattern **and** that the tag version equals
`pyproject.toml`'s version (closing #357's second ask).

| Pros | Cons |
|---|---|
| In-repo, reviewable, unit-testable, fleet-templatable | **Defeatable by editing the workflow** — the exact threat in §3(4) |
| Closes the tag↔version gap, which A does not | Runs after checkout; is a check, not an authorization boundary |

**Verdict**: worth doing as defense-in-depth and for the version-consistency value, but it is not a
substitute for A. Pairs naturally with a `tests/test_publish_*.py` lint gate, matching the existing
`test_publish_testpypi_verify.py` pattern.

### Option C — Bind the PyPI-side publisher to the environment

Set the Environment name field on each project's Trusted Publisher (both indexes). Makes A and B3
actually enforced rather than advisory. See §5.

**Verdict**: **required**, not optional. Cheap, owner-only, and without it A/B3 are decorative.

### Option D — Add a reviewer gate to `testpypi`

**Rejected against the stated requirement.** It would close the gap but forces a human into every
TestPyPI publish, breaking hands-free release-train operation — the opposite of the goal. A only
constrains *which ref*, which is the property we actually want.

### Option E — Remove `workflow_dispatch` from the publishers

Simplest possible fix, but removes the documented recovery path for a failed/non-retriable publish
against an immutable Release. With A in place, dispatch is already safe (tag-only), so E buys
little and costs operability.

**Verdict**: rejected; A subsumes it.

### Also recommended, independent of the above

**F — scope `id-token: write` to the publish jobs** (#357's third ask). Move the permission off the
workflow block onto the two publish jobs. Mechanical, low-risk, removes OIDC minting capability
from the build job entirely.

---

## 7. Recommendation

**C + A first (they are the actual control), then B and F as hardening.**

| Phase | Action | Scope | Reversible |
|---|---|---|---|
| P0 | Verify/settle the PyPI-side environment binding (D1) | 18 project↔index pairs | n/a (read) |
| P1 | Tag policies on `pypi` + `testpypi` | 8 repos × 2 envs | Yes — delete the policy or set `deployment_branch_policy: null` |
| P2 | Decide juniper-deploy's vestigial envs (D4) | 1 repo | Yes |
| P3 | In-workflow ref + tag↔version assert, with a lint gate | 7 publishers in ml, then fleet | Yes — revert the PR |
| P4 | Scope `id-token: write` to publish jobs | all publishers | Yes |

**Rollout order matters**: do P1 on **juniper-ml's `testpypi` only** first, then cut one throwaway
sub-package release to prove the tag policy admits a real release-train run end to end, before
touching `pypi` anywhere. A mistake on `testpypi` costs a failed rehearsal; a mistake on `pypi`
blocks a real release.

---

## 8. Verification plan

```bash
# state before/after (the sweep used for §2.1)
bash util/ad-hoc/2026-08-17_env_protection_sweep.bash

# per env, after P1
gh api repos/pcalnon/juniper-ml/environments/testpypi \
  --jq '.deployment_branch_policy'
gh api repos/pcalnon/juniper-ml/environments/testpypi/deployment-branch-policies \
  --jq '.branch_policies[] | "\(.type) \(.name)"'

# negative control — MUST fail at the environment gate, not publish
gh workflow run publish.yml --repo pcalnon/juniper-ml --ref main
gh run list --workflow publish.yml --limit 1     # expect the publish job blocked/failed

# positive control — a real release-train ceremony still completes hands-free to TestPyPI
```

The negative control is the acceptance test for this whole design: **a branch dispatch must not
reach TestPyPI.** Until that has been observed, P1 is not proven.

---

## 9. Owner decisions — **all four ANSWERED 2026-08-17**

- **D1 — Trusted Publisher environment binding. → CONFIRMED BOUND.** Every publisher config names
  its environment (`pypi` for PyPI, `testpypi` for TestPyPI), e.g. juniper-cascor /
  `publish-cascor-model.yml` / Environment name: `pypi`. **This is the finding that makes the rest
  load-bearing**: because PyPI checks the `environment` claim only when the publisher declares one
  (§5), and ours do, the GitHub-side environment gates are genuinely enforced rather than
  decorative. P1 was therefore worth applying.
- **D2 — Tag patterns. → `v*`, `juniper-*-v*`, plus `rc*`, `juniper-*-rc*`, `hf*`, `juniper-*-hf*`**
  added for future release-candidate and hotfix conventions. Six patterns, tag-type only.
- **D3 — Branch dispatch. → TAG-ONLY; `main` is NOT an allowed deploy ref.** Dispatching a
  publisher from any branch is refused at the environment gate. Recovery remains
  `gh workflow run publish.yml --ref <tag>`, already the documented procedure (`publish.yml:31`).
- **D4 — juniper-deploy. → DELETED.** Both `pypi` and `testpypi` environments removed
  (2026-08-17). Verified first that no juniper-deploy workflow referenced an environment and that
  both held zero secrets and zero variables. Only the unrelated `copilot` environment remains.

---

## 12. Implementation record (2026-08-17)

### 12.1 What was applied

| Change | Scope | Result |
|---|---|---|
| Tag policies (6 patterns, `type=tag`) | **16 publish environments** = 8 repos × {`pypi`, `testpypi`} | applied, verified |
| `deployment_branch_policy` → `custom_branch_policies: true` | same 16 | applied |
| Environment deletion | juniper-deploy `pypi` + `testpypi` | deleted |

Every `pypi` environment **retained** `reviewers(pcalnon)` + `wait(5m)`; the new
`branch_policy` rule is additive. Post-state captured by
`util/ad-hoc/2026-08-17_env_protection_sweep.bash`; applied by
`util/ad-hoc/2026-08-17_apply_env_tag_policies.bash` (dry-run default, idempotent).

### 12.2 Controls — both passed

**Negative control** (the acceptance test in §8) — `gh workflow run publish.yml --ref main`,
run `32069779425`:

```
Build and Validate:  completed/success
Publish to TestPyPI: completed/failure   <- 0 steps executed
Publish to PyPI:     completed/skipped
```

Annotation: **`Branch "main" is not allowed to deploy to testpypi due to environment protection
rules.`** The job recorded **zero steps**, i.e. it was refused *before starting* — no OIDC
credential was minted and no upload was attempted. This is the property an in-workflow `if:` cannot
provide.

**Positive control** — `gh workflow run publish.yml --ref v0.7.1`, run `32070020620`:

```
Build and Validate:  completed/success
Publish to TestPyPI: completed/success   <- tag admitted, full publish + verify
Publish to PyPI:     waiting             <- reviewer gate, as designed
```

The release path is intact. The run was cancelled at the PyPI reviewer gate rather than approved
(deploy approvals are the owner's). Together the two controls prove the policy discriminates on
ref, not on trigger.

### 12.3 A `PUT` caveat, tested rather than assumed

`PUT /repos/{owner}/{repo}/environments/{env}` is documented as create-or-update, which raised the
risk that a payload carrying only `deployment_branch_policy` would **clear** the reviewer and
wait-timer rules on the `pypi` environments. Verified empirically on a throwaway
`scratch-policy-test` environment (created with reviewers + wait timer, then PUT with the
branch-policy payload alone): the rules **survived** —
`rules: [required_reviewers, wait_timer, branch_policy]`. The scratch environment was deleted.
**Do not generalise this** to payloads that do carry `reviewers` / `wait_timer`.

### 12.4 Tag-coverage audit

All release tags across the 8 publishing repos were checked against the six patterns before rollout.
**80 of 82 matched.** The two exceptions are both dead juniper-ml one-offs from early 2026:

- `juniper-observability.v0.1.0a2` — a **dot** before `v`, where the convention uses a dash
- `juniper-v0.1.0-alpha` — no package segment between `juniper-` and `-v`

Neither is the live convention (`v<semver>` / `juniper-<pkg>-v<semver>`), both are historical, and
no future release would use either shape. **No live convention is blocked.** Re-run the audit if a
new tag shape is ever introduced — a too-strict policy blocking a real release is the failure mode
that matters most here.

### 12.5 Residual gaps (still open)

- **P3** — in-workflow ref + tag↔version assertion (Option B). Unstarted.
- **P4** — scope `id-token: write` to the publish jobs (Option F). Unstarted.
- **No drift gate.** Nothing prevents an environment policy from being removed later. A lint in the
  `test_*_workflow.py` family, or a scheduled run of the sweep script, would close this.
- `copilot` environments (ml / cascor / data-client / deploy) remain ANY-REF. They are unrelated to
  publishing and were deliberately left alone.

---

## 10. Relationship to the open issues

- **#358 / #357** — this document is their analysis. Their literal subject
  (`juniper-cascor-core`'s publisher) no longer exists in juniper-ml, but three of the flagged
  gaps survive verbatim: dispatch-bypasses-tag-guard, no tag↔version check, workflow-level
  `id-token`. Recommend re-scoping both issues onto this design rather than closing them as stale.
- **ml#1012 / ml#1011** — unrelated family (branch protection). Recorded here only to note that
  `RepositoryRole 5` bypass does **not** interact with environment protection: environment rules
  are not ruleset rules and have no bypass-actor list.

---

## 11. Sources

- [PyPI — Security Model and Considerations](https://docs.pypi.org/trusted-publishers/security-model/)
- [PyPI — Internals and Technical Details](https://docs.pypi.org/trusted-publishers/internals/)
- [PyPI — Adding a Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
- [pypi/warehouse#17241 — Environment claim included but not checked](https://github.com/pypi/warehouse/issues/17241)
- [GitHub — Managing environments / deployment protection rules](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub — Deployment branch policies REST API](https://docs.github.com/en/rest/deployments/branch-policies)
- [GitHub — Configuring OpenID Connect in PyPI](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi)
- [OpenSSF — Trusted Publishers for All Package Repositories](https://repos.openssf.org/trusted-publishers-for-all-package-repositories.html)
