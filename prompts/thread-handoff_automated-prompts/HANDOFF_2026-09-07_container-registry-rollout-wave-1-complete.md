# HANDOFF 2026-09-07 — Container registry rollout: Wave 1 published, and it ships CUDA

**Session**: X7 arc tail → cascor-client 0.8.0 release → container-registry publishing (Wave 1)
**Predecessor**: `HANDOFF_2026-09-05_x7-arc-tail-and-semver-minor-release.md`
**Validation**: 4 independent agents (2 Lane A entry points, 2 Lane B lenses) per
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
They returned **15 defects in the first draft**, including one product defect. All
corrections below were re-verified by the author before being applied.

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **container-registry rollout**. Wave 1 published, and validation found the
image ships the CUDA stack it was designed to exclude. Fix that first.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/` — `cd` there first. Every
relative path below is from there, EXCEPT paths beginning `notes/` or `prompts/`, which are
inside `juniper-ml/` (note `Juniper/notes/` also exists, so this matters).

**Order, ruled — items 1 and 3 are independent:**
`1 (fix CUDA) → re-dispatch → 2 (Pi pull on the FIXED image)`. Item 3 (Wave 2) runs in
**parallel** with item 1: it touches four other repos and does not depend on the worker fix.
Item 2 gates **Wave 3's pin**, not Wave 2. Do not pull the current 3 GB image to eight nodes
only to replace it.

**Definition of done for the arc**: all five images publish on `release: published`;
`juniper-deploy/docker-compose.yml` pins released `X.Y.Z` refs; and juniper-deploy's
pull-the-published-images integration test is green.

### Where this stands

`ghcr.io/pcalnon/juniper-cascor-worker:dispatch-3d81f2c` exists as a genuine multi-arch OCI
index and is **PUBLIC — anonymously pullable, no login required**:

```
mediaType: application/vnd.oci.image.index.v1+json
  linux/amd64      sha256:e619b1ec012e4724c4b5a12f69b89a74f3276d611bbaa93b5a01038c0e30ee6a
  linux/arm64      sha256:1bb497cdce41da7f9038e0433644033a831764c49ec691c822c132876ca514b9
  + 2 buildx attestation manifests (vnd.docker.reference.type: attestation-manifest)
```

It is the only Juniper image published anywhere (Docker Hub `pcalnon` namespace is empty;
the other nine names 404 on GHCR). There is no semver tag and no `latest` — the workflow
pushes on `release: published`, and no worker release has been cut since it merged (last is
**v0.5.0, 2026-07-23**). The `dispatch-<sha>` tag exists so the publish path could be
exercised without cutting one.

Design of record:
`juniper-ml/notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`
(merged, juniper-ml#1802). **It is on `origin/main` but the juniper-ml primary checkout is
behind and does not have the file — `git pull --ff-only` there first.**

Its decisions are settled; do not re-litigate. In one line each, so you need not fetch it
to know what you must not reopen: **D-1** publishing lives in the owning repo, on
`release: published`. **D-2** GHCR first, Docker Hub second. **D-3** release-only trigger;
tags `X.Y.Z` / `X.Y` / `latest`. **D-4** `linux/amd64` + `linux/arm64` for all five images.
**D-5** GPU/CUDA out of scope.

### Remaining work

**1. P0 — the worker image ships CUDA torch. Fix before anything reaches a Pi.**

The image is **2.99 GB (arm64) / 2.86 GB (amd64)** and contains `torch 2.12.1+cu130` plus
`nvidia-cublas`, `nvidia-cudnn-cu13`, `nvidia-nccl-cu13`, `triton`, `cuda-toolkit`. The
Dockerfile comment claims the CPU-only lock saves "~2-4 GB of image bloat". It does the
opposite. Verified causal chain, `juniper-cascor-worker/Dockerfile`:

```dockerfile
L25  RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
L29  RUN pip install --no-cache-dir -r requirements-cpu.lock     # <- NO index flags at all
```

- `requirements-cpu.lock` is compiled `--no-emit-package torch`, so torch is absent from it.
- It pins `juniper-cascor-model==0.1.0`, whose metadata declares `torch>=2.10.0`.
- L29 therefore re-resolves that unsatisfied requirement **from PyPI default**, gets the
  CUDA build, **uninstalls the CPU wheel from L25**, and drags in the NVIDIA stack.
- L25 is also **unpinned** — the CPU index currently serves 2.9.0 … 2.14.0.

Consequences: 3 GB per Pi node × 8+ nodes of disk and bandwidth for libraries a Pi can
never use, and **OQ-3 is understated** — it is a disk/bandwidth question, not only RAM.

**THE FIX, RULED** — do not treat this as a menu, because two of the three obvious
approaches fail and one of them fails *silently*:

> Add `--extra-index-url https://download.pytorch.org/whl/cpu` to **L29**, and pin torch to
> a `+cpu` local version. `requirements-cpu.lock` lines 8-20 already carry the exact
> regeneration recipe (`uv pip compile … --extra-index-url … --override torch==X.Y.Z+cpu
> --no-emit-package torch`); the lock honours it at compile time and the **Dockerfile does
> not** at install time. That mismatch is the whole bug.

Two approaches that look right and are not:

- **Reordering (lock first, CPU wheel last) is a VACUOUS FIX.** pip replaces `torch` but
  does not remove the orphaned `nvidia-cublas` / `nvidia-cudnn-cu13` / `nvidia-nccl-cu13` /
  `triton` it already pulled, and `Dockerfile:67` copies **all** of `site-packages` into the
  runtime stage. The image stays ~3 GB while `torch.__version__` reads `+cpu` — so a
  version assertion passes and the size never moves.
- **`--index-url` on L29 breaks the build.** It *replaces* the default index, and the
  PyTorch CPU index does not serve the rest of the lock: `pydantic` → 403, `websockets` →
  403 (`numpy` → 200). `--extra-index-url` is the working form.

**Assert the result in the `merge` job, not only the smoke step.** The smoke step is
`if: github.event_name != 'release' && !inputs.push` (`publish-image.yml:193`), so it never
runs on a publish; the merge job (the only publish-path check) currently verifies
architectures alone. A pinned-version assertion that lives only in the smoke step cannot
catch a regression on the path that actually ships.

**2. OWNER GATE — pull the image on a Raspberry Pi node.** Gates Wave 2. No login needed.

```bash
docker pull ghcr.io/pcalnon/juniper-cascor-worker:dispatch-3d81f2c
docker run --rm --entrypoint python \
  ghcr.io/pcalnon/juniper-cascor-worker:dispatch-3d81f2c \
  -c "import platform, torch; print(platform.machine(), torch.__version__)"
```

Expect `aarch64 2.12.1+cu130` **from the current image** — that is the defect in item 1, not
a fault in the pull. After item 1 ships, expect a pinned `+cpu` version and a far smaller
image. Consider gating on the fixed image instead, to avoid moving 3 GB twice.

**3. Wave 2 — replicate to the four remaining images.** Suggested order: **recurrence
first** (it is the one that crashes as written, so its problems surface while the pattern is
still malleable), then data, cascor, canopy. Reference:
`juniper-cascor-worker/.github/workflows/publish-image.yml` — 330 lines, read all of it; the
two load-bearing properties are at **L153** and **L171**, the `merge` job at **L240**.

Fetch it without git — a worktree-isolated session refuses `git -C <other repo>`:

```bash
gh api repos/pcalnon/juniper-cascor-worker/contents/.github/workflows/publish-image.yml \
  --jq .content | base64 -d > /tmp/publish-image.yml
```

**"Change only the image name" is wrong.** `IMAGE_NAME: ${{ github.repository }}` is derived
and already correct everywhere; what changes is the *local smoke tag* `worker-smoke:<arch>`
(two places). Per-repo, the following also change:

| | juniper-cascor | juniper-canopy | juniper-data | juniper-recurrence |
| --- | --- | --- | --- | --- |
| Release-tag guard | **REQUIRED** `v` | none | none | **REQUIRED** `juniper-recurrence-v` |
| `pull_request: paths:` src | `src/**` | **`src/**` AND `juniper_canopy/**`** | `juniper_data/**` | `juniper_recurrence/**` |
| Lock file in `paths:` | `requirements.lock` | `requirements.lock` | `requirements.lock` | **none exists** |
| Build context | repo root | repo root | repo root | **`juniper-recurrence/juniper-recurrence`** |
| `pyproject.toml` path | root | root | root | **nested — see below** |
| Base image | 3.14-slim | 3.14-slim | 3.14-slim | **3.13-slim** |
| ENTRYPOINT? | **no, CMD only** | **no, CMD only** | **no, CMD only** | yes |
| Actual `CMD` | `python src/server.py` | `python src/main.py` | `python -m juniper_data` | `serve` (after ENTRYPOINT) |
| Torch-bearing? | yes | **no** | **no** | check |

- **The tag guard is not optional and its absence is destructive.** `juniper-cascor` and
  `juniper-recurrence` are multi-package repos cutting several tag families. The worker
  workflow has no guard because it is single-package. Copied verbatim into cascor, a
  `juniper-cascor-model-v0.3.0` release fires the *service* image build and — because
  `type=raw,value=latest` is gated on `github.event_name == 'release'` but **not on the
  tag** — republishes `juniper-cascor:latest` from a model release. `type=semver` yields
  nothing there, so the zero-tag guard does not catch it. Their own publishers already do
  this: `juniper-cascor/.github/workflows/publish.yml:15` and
  `juniper-recurrence/.github/workflows/publish-recurrence-app.yml:73`.
- **recurrence needs a `type=match` tag rule**, not `type=semver` — `type=semver` cannot
  parse `juniper-recurrence-v0.4.0`, so a legitimate release would publish only `latest`
  with no version tag, and the verify step would inspect an empty ref.
- **recurrence's `Resolve build provenance` step will crash as written.** It runs
  `tomllib.load(open("pyproject.toml"))["project"]["version"]` from the repo root; there is
  no root `pyproject.toml`, and the nested one uses a **dynamic** version
  (`attr = "juniper_recurrence._version.__version__"`), so both the path and the read need
  changing.
- **The `paths:` filter is per-repo and its failure is silent.** The reference lists
  `requirements-cpu.lock` and `juniper_cascor_worker/**`, which exist in no other repo. Copy
  it unchanged and the PR that *introduces* the file still matches (via the workflow's own
  path) and goes green — then the arm never fires again. Vacuous-pass class.
- **The smoke test must change per repo, and deleting the import is not the fix.** Only
  worker and recurrence have `ENTRYPOINT`; cascor/canopy/data are `CMD`-only, so
  `docker run IMG python -c …` works directly and `--entrypoint python` is unnecessary,
  while the reference's second assertion `docker run IMG --help` would append `--help` to
  each repo's real `CMD` (see the table row) rather than invoking a console script — drop
  that assertion for the three CMD-only images or replace it with a real invocation.
  For canopy and data, which are **not** torch-bearing, the substitute arch assertion is
  `import pydantic_core, numpy` — those are the native wheels that must resolve per-arch,
  and they are what proves the arm64 build is real. Do not simply delete the import.
- **arm64 evidence does not transfer to recurrence.** The cp314 aarch64 wheel argument is
  ABI-specific; recurrence is `python:3.13-slim`. Re-check cp313 aarch64 wheels before
  assuming arm64 is cheap there.
- **Decide what happens to the existing CI docker-build jobs.** canopy, cascor, data and
  recurrence-app each already build and smoke-test an image, then discard it. Wave 2 adds a
  second build per repo. Retire, dedupe, or accept the doubled cost — but decide.

**Acceptance for each Wave 2 PR**: the PR arm builds *both* arches and both smoke tests
pass; then a `workflow_dispatch` with **`push: true`** (the input defaults to `false`)
produces `dispatch-<sha>` and the `merge` job's arch verification passes.

⚠ **That dispatch is the only public, irreversible action in this document** — it creates a
new GHCR package per repo, and all five repos are public so the packages inherit public
visibility. **Confirm with the owner before the first one.** (A session's `gh` token
typically lacks `read:packages`, so you cannot audit existing packages to check.)

⚠ **Do not register `publish-image` as a required status check.** It is `paths:`-filtered,
so requiring it would leave every unrelated PR in that repo waiting forever on a context
that never runs — the same orphaned-check failure mode as a CI-skip marker.

**4. Wave 3 — juniper-deploy repin. BLOCKED until all FIVE image-bearing repos cut a
release** (the worker included — its last is v0.5.0, 2026-07-23, predating the workflow).
There is no pinnable ref today. Chain: Wave 2 merged → a release cut per repo → pin.
Detect with `gh release list --repo pcalnon/<repo>` across worker, cascor, canopy, data,
recurrence. **Cutting those releases is an owner action and appears nowhere on this list.**

- `docker-compose.yml` has **13 `image:` lines, 9 of them Juniper**, mapping to **5 unique
  images**: canopy ×3 (L620/764/855), cascor ×2 (L197/391), **data ×2 (L134 and L487)**,
  worker ×1 (L334), recurrence ×1 (L556). The three canopy services share identical `build:`
  args and differ only in `environment:`, which is why one image serves all three.
- **`demo-seed` (L487) has no `build:` stanza** — it reuses the data image and overrides
  `entrypoint:`. "Keep `build:`" is inapplicable there; decide explicitly, because skipping
  it leaves `juniper-data:latest` unbuilt once the data service's `build:` is retagged.
- **Unstated hazard in "keep `build:`":** once `image:` is a published release ref, a local
  `docker compose build` stamps the **dev tree** with the **release tag**, and later
  `docker compose up` silently prefers it. That is exactly what `make doctor`'s stale-image
  detection exists to catch. The plan calls Wave 3 "deliberately low-risk"; this is the
  risk it does not name.
- **Wave 3 also owes two things the plan assigns juniper-deploy and this handoff nearly
  dropped** (D-1, plan L68-70): publishing its **own `Dockerfile.test` runner** (a sixth
  image; context already at `docker-compose.yml:1061`), and an **integration test that
  pulls the published images** — the only end-to-end consumer check in the design.

**5. Wave 4 — Docker Hub** as a second push target. Needs `DOCKERHUB_TOKEN` per repo.
Answer OQ-1 first.

**6. Owner decisions — surface, do not guess** (plan §6): **OQ-1** Docker Hub posture for
multi-GB images; **OQ-2** a `:X.Y.Z-cuda` variant (note item 1 makes today's image
accidentally CUDA — that is a bug, not OQ-2 being answered); **OQ-3** Pi capacity, now
disk/bandwidth as well as RAM; **OQ-4** a versioned stack manifest.

### Key context — settled; do not re-litigate

- **Publishing lives in the OWNING repo, on `release: published`.** The deciding question is
  what a tag *means*: this makes image tag ≡ PyPI version ≡ git tag by construction.
  juniper-deploy cannot — it does not know when a sibling cuts a release. (D-1.)
- **GHCR needs no secret**: `GITHUB_TOKEN` + `packages: write`. (Do not cite "it worked on
  the first attempt" as proof — the step was *skipped* on both PR runs and first executed in
  dispatch run 34027026254. The conclusion is right; that particular proof was not.)
- **arm64 is not emulated and is consistently faster**, but quote the publish run, not the
  cheapest one. Build-step times: cold-cache PR run 13m08s arm64 / 15m14s amd64; warm PR run
  7m37s / 10m18s; **the actual publish (34028226714) 11m43s arm64 / 16m04s amd64**.
- **Both workflow properties are load-bearing — do not simplify when replicating.**
  (1) Tags are written exactly once by the `merge` job; both arches push *by digest*, so no
  two jobs race for a tag. (2) The `pull_request` arm builds both arches and pushes nothing.
- **GPU is out of scope by design** — no `runtime: nvidia`, no device reservations anywhere
  in the container path (the `reservations:` blocks are CPU/memory only). Item 1 is an
  accident, not a GPU strategy.
- **The item that opened this arc was mis-specified.** "`image: juniper-canopy:latest` wants
  a pinned release tag" — it does not; with no registry that is a local build-output tag.

### Traps that cost this session time

- **`ENTRYPOINT` swallows a `docker run` command** — but only 2 of 5 images have one
  (worker, recurrence). `docker run IMG python -c …` needs `--entrypoint python` there and
  nowhere else.
- **A digest push cannot carry a tag.** `push-by-digest=true` + `tags:` fails with
  `can't push tagged ref docker.io/library/worker-smoke:amd64 by digest`.
- **`${{ cond && '' || 'x' }}` IS NOT A TERNARY.** GitHub's `&&`/`||` only behaves as one
  when the true-branch is **truthy**; `''` is falsy, so `||` falls through and yields `'x'`
  in both branches. Use two `if`-gated steps.
- **A 401 from GHCR proves nothing about visibility.** Every GHCR repo returns 401 to a bare
  GET, public or private (`astral-sh/uv` does). The discriminating instrument is whether an
  **anonymous token** is issued *and honoured* — see Verification.
- **`conda run -n JuniperCanopy1`, never the env's binary path.** The direct path skips the
  hooks stripping `rust_mudgeon` LIBTORCH; `import torch` then dies on
  `undefined symbol: _PyObject_NextNotImplemented` and cascades into **101 failures across
  20 unrelated files**, reading like a broad regression rather than an environment fault.
- **`pre-commit run --files X` green is about PATH SCOPE, not the repo.** CI runs
  `--all-files`; `end-of-file-fixer` caught a file that passed `--files`.
- **`git branch --merged` returns nothing for squash-merged branches.**
  `gh pr view N --json state` is the authoritative merge test.
- **`gh run view --log` intermittently returns empty.** Use
  `gh api repos/O/R/actions/jobs/<id> --jq '.steps[]'` and `.../check-runs/<id>/annotations`.

### Corrections to the predecessor

`HANDOFF_2026-09-05` said canopy#582 was `BEHIND` and "should land on its own". It was
`BLOCKED` on a failing Sequence Safety check — a same-file test rename read as symbol loss —
and needed an `Allow-Symbol-Loss` trailer, not patience. (Verified: the waiver commit and
trailer are on that PR.)

Its carrier *count* was four where five files changed, but it **did** instruct the
`CHANGELOG.md` re-head in the same item — an under-count, not an omission. And of the two
`AGENTS.md` CI guards, only one reads the **version**; the other checks the
**Last-Updated date**.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper

# Visibility — the DISCRIMINATING test (a bare GET returns 401 for everything)
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-cascor-worker:pull&service=ghcr.io" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-cascor-worker/tags/list
#   -> {"tags":["dispatch-3d81f2c"]}   ; the same flow against juniper-canopy -> DENIED

# The published manifest, no credentials at all
docker manifest inspect ghcr.io/pcalnon/juniper-cascor-worker:dispatch-3d81f2c

# Item 1: prove the CUDA regression without pulling 3 GB
grep -n 'no-emit-package torch' juniper-cascor-worker/requirements-cpu.lock
grep -n 'juniper-cascor-model==' juniper-cascor-worker/requirements-cpu.lock
curl -s https://pypi.org/pypi/juniper-cascor-model/0.1.0/json \
  | python3 -c "import sys,json;print([r for r in json.load(sys.stdin)['info']['requires_dist'] if 'torch' in r])"
sed -n '18,30p' juniper-cascor-worker/Dockerfile      # L29 has no index flags
sed -n '1,22p' juniper-cascor-worker/requirements-cpu.lock   # the +cpu recipe the build ignores
grep -n 'COPY --from=builder' juniper-cascor-worker/Dockerfile  # L67: copies ALL site-packages
for p in pydantic websockets numpy; do
  printf '%-12s ' "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://download.pytorch.org/whl/cpu/$p/"
done   # 403 / 403 / 200 -> why --index-url breaks and --extra-index-url is required

# The workflow to replicate — ALL of it. Use the API form: a worktree-isolated session
# refuses `git -C <other repo>`, and the local checkout is 2 commits behind and still
# carries the PRE-#173 workflow (the exact bug the digest/tags trap describes).
gh api repos/pcalnon/juniper-cascor-worker/contents/.github/workflows/publish-image.yml \
  --jq .content | base64 -d > /tmp/publish-image.yml
gh api repos/pcalnon/juniper-cascor-worker/commits/main --jq '.sha[0:7]'   # expect 777e657+
```

### Git state

Every PR from this arc is **merged**, and no arc worktree holds uncommitted changes.

This handoff lives at
`juniper-ml/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md`
and was landed by its own PR; if you are reading it from a checkout that predates that
merge, `git pull --ff-only` in juniper-ml.

| Repo | PRs merged |
| --- | --- |
| juniper-cascor-client | #155 (0.8.0 bump), #156 (notes finalized), #157 (CHANGELOG order) |
| juniper-canopy | #582 (demo-mode honesty), #584 (cap `<0.9.0`), #591 (floor `>=0.8.0`) |
| juniper-cascor-worker | #172 (publish-image.yml), #173 (digest/tags fix) |
| juniper-ml | #1779, #1788 (release-notes archive), #1792 (ad-hoc tool), #1802 (design of record) |

`juniper-cascor-client 0.8.0` is on PyPI. **`juniper-cascor-worker` main is `777e657`**
(#174, a dependabot bump, merged after this arc); `3d81f2c` is its parent and is the commit
the published image was built from — those are different facts.

**The local `juniper-cascor-worker` checkout is 2 commits behind and still contains the
pre-#173 workflow**, which will mislead anyone reading it directly. `git fetch` first.

**Leave every worktree alone** — cleanup is a separate, owner-signalled step, and
`worktree remove` deletes ignored files silently. Listed for orientation only. Three arc
worktrees remain (all clean, all with merged PRs), plus two older worker worktrees from
earlier arcs (`--docs--handoff-word-count--…`, `--fix--mv-screened-base--…`).

```
worktrees/juniper-cascor-worker--feat--publish-container-image--20260905-1846--1080015f   [fix/publish-image-digest-tags]
worktrees/juniper-cascor-client--docs--changelog-section-order--20260905-1523--714e544a   [docs/changelog-0.8.0-section-order]
worktrees/juniper-canopy--chore--pin-cascor-client-floor--20260905-1441--482281ac         [chore/pin-cascor-client-floor-0.8.0]
```

Local branches `feat/publish-container-image` and `fix/publish-image-digest-tags` survive in
juniper-cascor-worker, and both remotes are still on GitHub.

### Conventions for landing items 1 and 3

Item 1 lands in **juniper-cascor-worker**; Wave 2 lands in **four further repos** — none of
them juniper-ml, so juniper-ml's `AGENTS.md` is not the loaded guidance for any of it. Read
each target repo's own `AGENTS.md`, and follow
`notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md` for the centralised
worktree location and the `<repo>--<branch>--<YYYYMMDD-HHMM>--<sha8>` naming. PR base must
be the default branch — a required check enforces it.

---
