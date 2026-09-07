# Container Registry Publishing — Design of Record

**Project:** Juniper (ecosystem-wide)
**Author:** Paul Calnon
**Date:** 2026-09-05
**Status:** ACCEPTED — decisions ratified by the owner 2026-09-05; Wave 1 (pilot) in flight
**Scope:** publishing the five Juniper service images to container registries

---

## 1. Why this exists

`juniper-deploy/docker-compose.yml` carries nine `image:` lines, every one of them
`<name>:latest`, and every one paired with a `build:` stanza pointing at a **sibling
working copy** (`context: ../juniper-canopy`). Nothing is published anywhere.

That has three consequences worth naming, because only the first is obvious:

1. **The stack cannot be run on a machine that is not this workstation.** Every host needs
   all sibling repos checked out at compatible commits before `docker compose up` means
   anything.
2. **`:latest` is not a version.** It names whatever the local build produced, so two hosts
   running "the same stack" have no way to discover that they are not.
3. **The tag pin that was filed as the fix is not one.** The deferred item entering this
   work read *"`image: juniper-canopy:latest` wants a pinned release tag."* It does not:
   with no registry, `juniper-canopy:latest` is a **local build-output tag**, and renaming it
   `v0.9.0` would change nothing about what the build contains. The real question was
   whether Juniper should publish images at all, which is what this document answers.

## 2. What already exists (the work is smaller than it looks)

Measured 2026-09-05, not assumed:

| Fact | Consequence |
| --- | --- |
| Nine `image:` lines are **five unique images** (canopy ×3 full/demo/dev, cascor ×2 main/demo) | Five workflows, not nine |
| canopy, cascor, data and recurrence-app **already build their image in CI**, smoke-test it, and discard it | This is "keep the artifact", not "add a build" |
| Dockerfiles already carry full OCI labels, incl. `org.opencontainers.image.source` | GHCR repo-linking works with no Dockerfile change |
| Dockerfiles already accept `GIT_SHA` / `BUILD_DATE` / `APP_VERSION` build args | Provenance is already wired; compose already passes them |
| All repos are **public**; every service repo publishes to PyPI on `release: published` | GHCR is free, and a uniform release event already exists |
| juniper-deploy has **no service Dockerfiles** — only `Dockerfile.test` | It is a consumer, not a producer, of service images |

## 3. Decisions

### D-1 — Publishing lives in the **owning repo**, not in juniper-deploy

Each service repo publishes its own image on its own `release: published` event.

**Why.** The deciding question is not where credentials live, it is **what a tag means**.
The repos already have release-driven versioning: Release → tag → `publish.yml` → PyPI.
Publishing images on that same event makes **image tag ≡ PyPI version ≡ git tag by
construction**, not by a convention someone must remember.

juniper-deploy cannot do that. It does not know when canopy cuts a release, so publishing
from there yields either tags meaning "whatever main was that day", or a cross-repo
dispatch mechanism to learn about releases — machinery whose only purpose would be to
recover information the owning repo already has.

Two supporting reasons: the `org.opencontainers.image.source` label already names the
owning repo (publishing elsewhere would either misstate provenance or require changing it),
and GHCR from the owning repo needs **no secret at all** — `GITHUB_TOKEN` with
`packages: write`.

**The rejected alternative's one real advantage** was centralising the *Docker Hub*
credential in a single repo instead of four. That is genuine but small: GHCR needs none,
and four `gh secret set` calls are scriptable for rotation.

**juniper-deploy keeps a real role:** it publishes its own `Dockerfile.test` runner, pins
the consumed tags, and becomes the natural home for an integration test that pulls the
**published** images — a stronger check than building from `../sibling` paths.

### D-2 — GHCR first, Docker Hub second

Phase 1 targets `ghcr.io/pcalnon/<image>` only. Phase 2 adds a second login+push to
`docker.io/<user>/<image>` in the same workflow.

**Why.** GHCR needs no provisioned secret, so phase 1 proves the whole pipeline —
multi-arch build, digest merge, manifest verification, consumption from compose — with
zero credential surface. Docker Hub then becomes a second push target against a tagging
scheme already settled, rather than a variable in the same experiment.

Note for phase 2: cascor and cascor-worker are torch-bearing and therefore multi-GB.
Docker Hub's storage and pull-rate posture for a personal account should be checked before
that push is added, not after.

### D-3 — Release-only trigger; tags `X.Y.Z`, `X.Y`, `latest`

**Why.** Mirrors the PyPI discipline exactly: only released code is published, so nothing
unreviewed reaches a registry and every tag is reproducible from a git tag. A `:main` /
`:edge` arm was considered and rejected for now — it would push multi-GB torch images on
every merge for a consumer that does not yet exist.

### D-4 — `linux/amd64` **and** `linux/arm64`, for all five images

**Why — the fleet requires it.** The consuming hosts are:

| Host | Arch | Role |
| --- | --- | --- |
| Raspberry Pi cluster, 8+ nodes (Ubuntu RasPi image or 64-bit RaspiOS) | arm64 | cascor-workers; ideally **any** stack component |
| This workstation (Ubuntu) | amd64 | multiple isolated full stacks; **GPU, natively** |
| Intel MacBook (macOS ≤ Sequoia) | amd64 | full stack; multiple workers |
| Additional server (Ubuntu server/workstation) | amd64 | full stack, components, or workers |

An amd64-only worker image simply would not run on the cluster the component exists to
feed. Uniform multi-arch is chosen over "arm64 only where it is cheap" because the Pi nodes
should be able to run any component, and a two-tier rule is one nobody remembers.

**Why it is cheap — this was the objection, and it was measured before being accepted.**
The natural fear is that torch compiles for hours under QEMU. Both halves are false:

* `torch-2.11.0+cpu-cp314-cp314-manylinux_2_28_aarch64.whl` **exists** on the PyTorch CPU
  index and matches the images' `python:3.14-slim` ABI. torch is downloaded, never built.
* The two pins that could **not** fall back to a source build both ship cp314 aarch64
  wheels: `pydantic-core==2.46.4` — which needs Rust, absent from a slim image, so a
  missing wheel would be a *hard failure* rather than a slow one — and `numpy==2.4.4`.
* `requirements-cpu.lock` carries no `platform_machine` markers and no arch-specific pins.
* There is **no emulation at all**: `ubuntu-24.04-arm` is GA and free for public repos, so
  each arch builds on its own native runner and the digests are merged afterwards.

### D-5 — GPU is out of scope, and that is not a deferral of something already working

Nothing in the container path touches GPU today: `docker-compose.yml` has no `runtime:
nvidia`, no device reservations, and the cascor / worker Dockerfiles install CPU-only torch
*deliberately* (`# Install CPU-only PyTorch first (avoids pulling CUDA which is ~4 GB)`).
Workstation GPU work runs natively in conda envs.

So multi-arch CPU images regress nothing. A `:X.Y.Z-cuda` variant is a **separate
decision**: it doubles the build matrix for the two torch images and adds multi-GB CUDA
layers, in exchange for a containerised GPU path that does not exist yet.

## 4. The workflow pattern

Reference implementation:
`juniper-cascor-worker/.github/workflows/publish-image.yml` (juniper-cascor-worker#172).

```
on:
  release: [published]      -> build BOTH arches, push by digest, merge, tag
  pull_request:             -> build BOTH arches, push NOTHING, smoke-test each
  workflow_dispatch:        -> opt-in push for a manual dry run

permissions: { contents: read, packages: write }     # no secrets

build   (matrix: ubuntu-24.04 / ubuntu-24.04-arm)    push-by-digest
merge   (needs: build)                               imagetools create + verify
```

Two properties are load-bearing and should survive replication:

**Tags are written exactly once.** Both arch jobs push **by digest**; only the `merge` job
applies tags. Two jobs pushing the same tag would race, and the loser's arch would vanish —
leaving a single-arch image wearing a multi-arch tag, which fails only on the host that
needs the other arch.

**The `pull_request` arm is not decoration.** A release-only workflow's first run is
otherwise also its first test: a broken Dockerfile or a missing arm64 wheel would surface
*on the tag*, at deploy time, with no way to fix it in place. Building both arches on every
PR that touches image inputs makes the build the test and leaves only the push gated on the
release.

The merge job additionally inspects the manifest and fails unless it lists exactly
`amd64,arm64`. A manifest that exists is not a manifest that is complete, and the place not
to discover that is on a Pi.

## 5. Rollout

| Wave | Repo | Status |
| --- | --- | --- |
| 1 (pilot) | juniper-cascor-worker | **in flight** — juniper-cascor-worker#172 |
| — | *verify: pull and run on a Pi node* | gate before Wave 2 |
| 2 | juniper-cascor | pending |
| 2 | juniper-canopy | pending |
| 2 | juniper-data | pending |
| 2 | juniper-recurrence | pending — build context is **nested** (`juniper-recurrence/juniper-recurrence/`) |
| 3 | juniper-deploy — pin `image:` to registry refs, keep `build:` for local dev | pending |
| 4 | Docker Hub as a second push target (D-2 phase 2) | pending |

The worker is the pilot because it has the only committed arm64 consumer and carries the
constraint most likely to break arm64. Proving it there de-risks the other four.

**Wave 3 is deliberately low-risk.** Compose keeps both keys: `image:` becomes the pinned
registry ref and `build:` stays. `docker compose build` then tags the local build with the
registry name, and `docker compose pull` fetches the published one — both workflows keep
working, and local development does not require a registry round-trip.

## 6. Open questions

- **OQ-1.** Does Docker Hub's personal-account posture (storage, pull limits) suit multi-GB
  torch images? Decide before Wave 4, not during it.
- **OQ-2.** Should a `:X.Y.Z-cuda` variant exist for cascor / cascor-worker, and if so is it
  built on release or on demand? (D-5.)
- **OQ-3.** Do the Pi nodes have enough RAM to run a torch-bearing worker in practice? This
  is a capacity question, not an architecture one — the image will run.
- **OQ-4.** Should juniper-deploy publish a versioned "stack manifest" (a pinned tag set)
  alongside the compose file, so a host can reproduce an exact stack from one identifier?
