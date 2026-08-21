# Snapshot storage convention — design of record

**Project**: Juniper — snapshot lifecycle management (F-P1-4)
**Sub-Project**: juniper-cascor / juniper-deploy / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-20

**Status**: DESIGN OF RECORD — **S-1 is ANSWERED**, and this document records the ruling, derives the
consequences, and enumerates the work. Supersedes the S-1 open question in
[`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)
§9 and the three options weighed in
[`JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-ROOT-LOCATION-DECISION-BRIEF.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-ROOT-LOCATION-DECISION-BRIEF.md)
(juniper-ml#1197).

Implemented by **juniper-cascor#545** and **juniper-deploy#189**.

> **This document failed its own review, and the correction is the most useful thing in it.**
> The first draft's headline claim — that the hyphen in `cascor-snapshots` makes the directory
> structurally undiscoverable by setuptools — is **false**. Three independent agents refuted it and
> the refutation was reproduced directly. §1.1 now records what actually provides the guarantee
> (`namespaces = false`) and demotes the hyphen to defence in depth. Two further claims were wrong in
> the same draft; both are corrected in place and flagged. Same failure class the snapshot arc has
> hit repeatedly: **a correct mechanism paired with a wrong consequence**.

---

## 1. The convention

**`<repo>/<short-repo-name>-snapshots/`** — for juniper-cascor, `juniper-cascor/cascor-snapshots/`.

One root, shared by **every** stack origin on a host:

| origin | how it reaches the root |
|---|---|
| direct CLI | `constants_hdf5.py` default (import-time); `JUNIPER_CASCOR_SNAPSHOTS_DIR` overrides |
| service (host / systemd) | `manager.py::_get_snapshots_dir` default (call-time); same override |
| container (compose) | **bind mount** of the host root + `JUNIPER_CASCOR_SNAPSHOTS_DIR` set explicitly |
| container (k8s / Helm) | PVC at the same in-container path — **an accepted exception**, see §5.1 |

Canopy is a **reader** of this root, not a separate store — see §4.3.

**Superseded, removed from code, config, and docs:**

- `<repo>/src/cascor_snapshots/` — the historical direct-CLI root. Emptied on disk; its 47 tracked
  artifacts were removed from git in juniper-cascor#544.
- `<repo>/snapshots/` — the service root introduced by juniper-cascor#537 (merged **2026-08-19**) and
  discarded by this ruling. It never held a file.
- `<repo>/src/snapshots/*.h5` — artifacts inside the importable serializer package. The package
  (7 source modules) stays; artifacts never return there.

### 1.1 What actually keeps the archive out of the distribution

**`namespaces = false` in `[tool.setuptools.packages.find]`.** That is the structural guard, and it
is now in `juniper-cascor/pyproject.toml`.

> ⛔ **RETRACTED — the first draft of this section said the opposite.** It claimed
> `cascor-snapshots` "is not a valid Python identifier, so setuptools can never discover the
> directory as a package … a naming property that they cannot [undo]", and called it "the single
> highest-value detail in the rename". **False.** pyproject's find defaults to `namespaces = true`
> (PEP 420); `PEP420PackageFinder._looks_like_package` is literally `return True`, and the only name
> filter rejects dots, not hyphens. Reproduced:
>
> ```
> $ python -c "from setuptools import find_namespace_packages; print([p for p in find_namespace_packages(where='.') if 'snapshot' in p])"
> ['cascor-snapshots', ...]
> $ python -c "import importlib; print(importlib.import_module('cascor-snapshots'))"
> <module 'cascor-snapshots' (namespace) ...>
> ```
>
> A wheel built with cascor's exact config carries `cascor-snapshots` in `top_level.txt`. The hyphen
> changed nothing about discovery.

With `namespaces = false`, discovery drops exactly eleven directories that were being treated as
packages — `cascor-snapshots`, `conf`, `data`, `docs`, `images`, `logs`, `notes`, `scripts`, `util`,
**and the sibling distributions `juniper-cascor-model` / `juniper-cascor-protocol`**, which publish
their own wheels and must never ship inside this one — while keeping all 29 real packages (every
directory carrying an `__init__.py`). Measured both ways; nothing legitimate is lost.

**The hyphen stays, as defence in depth.** It genuinely blocks the `import cascor_snapshots`
statement form and is skipped by plain `find_packages`. It is simply not the load-bearing part, and
describing it as a guarantee is what let a false claim into two merged PRs' worth of adjacent text.

**And C-6 has a third leg the draft also mis-attributed**: no `.h5` reaches a wheel or sdist because
there is **no `MANIFEST.in`** in either distribution and no SCM file-finder plugin — not because of
the directory name. One line of `graft cascor-snapshots` would put the archive in both, hyphen or no
hyphen. Pinned by `TestPackagingExcludesArtifacts`.

---

## 2. The owner's constraints, and what each one forbids

Recorded in effect, because a later reader will otherwise re-propose the rejected option.

| # | Constraint | What it rules out |
|---|---|---|
| **C-1** | Snapshots are **Juniper project assets** and must be captured by the external full-binary-offline-backup that archives the whole project directory tree. | Any root outside `Juniper/` — `~/.local/state`, `/var/lib`, a Docker named volume, a k8s PVC: none is visible to a tree walk. |
| **C-2** | Restore from the offline archive must be **copy + extract → full functionality**. | Any location needing a second, separately-documented step, or that must dodge collisions inside a user's dotfile tree. |
| **C-3** | Snapshots are **shared artifacts** across stack instantiations, and stacks may be **service, CLI, or containerised in any combination over time**. Stack-origin agnosticism supports collaboration across systems, servers, clusters, and researchers. | Any per-origin root; any container-private storage. Per-run roots remain available as an **override**, never as the default. |
| **C-4** | Snapshots must be **excluded from the repos**. | Tracking artifacts; an ignore rule that matches by filename rather than location. |
| **C-5** | Snapshots must be **protected from deletion**. | `docker compose down -v`-destructible storage; unguarded glob-and-delete tooling. |
| **C-6** | Snapshots must **not ship on PyPI**. Transfer between hosts/clusters/users is **strictly out-of-band and user-driven**. | Packaging the directory in any wheel or sdist; any implicit sync or mirror. |

**C-1 and C-3 together are what make the in-checkout location correct rather than merely
acceptable.** A backup that walks `Juniper/` captures the archive for free, and a single host path is
the only thing all origins can agree on without configuration.

---

## 3. Design

### 3.1 Host — direct CLI and service

Both defaults resolve to `<cascor repo root>/cascor-snapshots`, created on demand.
`JUNIPER_CASCOR_SNAPSHOTS_DIR` overrides both (W-6), blank-is-unset intact. The direct CLI resolves at
**import** time (so an override must be exported before the first `cascor_constants` import); the
service resolves at **call** time. That asymmetry is pre-existing and unchanged.

The directory is **tracked** via `cascor-snapshots/.gitkeep` — see §4.2 for why that is load-bearing
rather than cosmetic.

### 3.2 Container (compose) — bind mount, not a named volume

```yaml
    environment:
      JUNIPER_CASCOR_SNAPSHOTS_DIR: /app/cascor-snapshots
    volumes:
      - ${JUNIPER_CASCOR_SNAPSHOTS_HOST_DIR:-../juniper-cascor/cascor-snapshots}:/app/cascor-snapshots
```

Four properties, each tied to a constraint:

1. **Survives `docker compose down -v`** (C-5) — and `make clean`, which runs `down -v --rmi local`
   behind one confirmation prompt. A named volume survives neither.
2. **Shares one archive with host stacks** (C-3).
3. **Inside the backup tree** (C-1, C-2).
4. **The container path is declared, not derived.** This is the fix for the defect the brief called
   F-1: the service computed `parents[3]/"snapshots"` = `/app/snapshots` while the volume mounted
   `/app/data`, one directory away, so **every containerized snapshot went to the container's
   writable layer and died on recreate** — silently, since the save path only warns. The CLI tier had
   a *third* path, `/app/src/cascor_snapshots`. `ENV JUNIPER_CASCOR_SNAPSHOTS_DIR` is now set in the
   **image**, so a bare `docker run` and the Helm path are right by default and orchestrators only
   mount over an already-correct path.

**This is a deliberate departure from the compose file's own convention.** Today that convention is
*config in via a read-only in-project bind; data out via a named volume* — there is no other
read-write bind, no bind whose source leaves the project directory, and no `../` in any `volumes:`
entry (the nine `../` paths are all `build.context`). No named volume can satisfy C-1 or C-5, so the
departure is correct — but it is recorded here and in the deploy CHANGELOG so a later reviewer does
not tidy it back.

**Relative-path semantics.** Compose resolves a relative bind source against the **compose project
directory**, exactly like `build.context`. The difference is the failure mode: a wrong build context
fails loudly (no Dockerfile), while a wrong bind source is **created by the daemon, root-owned**, and
the stack comes up healthy over an empty archive. `--project-directory`, an absolute `COMPOSE_FILE`
override, or running from a copy of the repo all relocate it. `make snapshot-preflight` exists for
exactly this and is wired into every bring-up target; it caught the failure on its first run against
a worktree checkout. A bare-name value (no `./` or `../`) is read as a *named volume* and fails
closed with `refers to undefined volume`.

**Ownership.** The image creates `juniper` as uid/gid 1000:1000 (`Dockerfile:56-57`) and runs as it
(`:71`); the host account is also 1000:1000, so the bind lands writable with no `user:` override.
Two caveats, both real (§6): a host whose account is not uid 1000, and rootless Docker, where the
correct setting **inverts** to `user: "0:0"`. Note that `user: "${UID:-1000}:${GID:-1000}"` is a
**no-op** — bash does not export `UID` and never defines `GID`, so both defaults always fire.

### 3.3 Packaging — the wheel must not resolve a root inside the Python tree

Two distinct problems.

**(a) The directory must not be packaged.** Satisfied by `namespaces = false` (§1.1), the absence of
any `MANIFEST.in` or SCM file-finder plugin, and the directory holding no `.py`. Not by the hyphen.

**(b) The default must not *resolve* into the Python tree.** `cascor_constants` is vendored verbatim
into the published `juniper-cascor-model` (installed top-level per its `pyproject.toml`) and
byte-gated by `juniper-cascor-model/tests/test_drift.py`. Naive repo-root resolution makes this
**worse**, not better:

```text
BEFORE (src-relative)    <site-packages>/cascor_snapshots
NAIVE  (root-relative)   <python-lib>/cascor-snapshots      ← escapes site-packages entirely
```

**Shipped resolution**, identical in both copies:

1. `JUNIPER_CASCOR_SNAPSHOTS_DIR` if set and non-blank.
2. `<project dir>/cascor-snapshots` when the module was **not** imported from an install tree.
3. Otherwise `<cwd>/cascor-snapshots`, with a `RuntimeWarning` naming the variable.

The install-tree test is `sysconfig` `purelib`/`platlib` containment — stdlib-only, no subprocess,
and exact. **A `pyproject.toml`-adjacency probe was considered and rejected**: it answers *wrongly*
inside the container, whose runtime stage copies only `src/`, so `/app/pyproject.toml` does not
exist. Step 3 is a weak default on its own, which is why every deployed path now declares the
variable explicitly (compose, the systemd unit, the image `ENV`) — reaching step 3 means genuinely
unconfigured, and a warning that names the variable beats silently writing into the interpreter's
library directory.

> ⛔ **RETRACTED — the first draft justified byte-identity with a false fact.** It said "the
> 2026-08-19 re-extraction deliberately emptied that set" of `_INTENTIONAL_DIVERGENCE`. **The set
> that was emptied is `_NORMALIZED_DIVERGENCE`.** `_INTENTIONAL_DIVERGENCE` still holds
> `log_config/logger/logger.py` (`test_drift.py:31`) — and its comment describes *the same problem
> being solved here*: a packaged copy whose source-relative default is unwritable in site-packages.
> So the cost of the divergence alternative was one *additional* entry, not the first. It happens
> that the `sysconfig` test makes byte-identity viable anyway, so the conclusion survives — but it
> was reached by an argument that did not.

### 3.4 Deletion protection (C-5) — the honest table

| Threat | Mitigation | Structural? |
|---|---|---|
| `docker compose down -v` / `make clean` | bind mount, not a named volume (§3.2) | yes |
| a cleanup glob deleting code | the root holds no `.py` | yes |
| accidental commit | `.gitignore` `/cascor-snapshots/*` — directory-anchored (§4.2) | yes |
| **`snapshot_cli cleanup`** | **was unmitigated**; now dry-run by default (`--yes` to apply) and refuses the shared root outright | yes, as of cascor#545 |
| **`git worktree remove`** | `worktree_cleanup.bash` now **refuses** a worktree holding `.h5`, with a `WORKTREE_CLEANUP_DISCARD_SNAPSHOTS=1` opt-out | procedural |
| `git clean -xdff` | a nested empty `.git/` inside the root would demote this from `-xdf` to `-xdff`; **declined** — the guard is obscure enough to confuse the next reader more than it protects | no, by choice |
| future retention tooling | design §6.4 contract: `--dry-run` default, `--yes` required, refuse outside a configured root, refuse a directory containing `.py` | procedural |

> ⛔ **RETRACTED — the first draft's table was wrong twice.** It listed retention tooling as a
> *future* concern while `HDF5Utils.cleanup_old_files` (`src/snapshots/snapshot_utils.py`) was
> already shipping, reachable from `snapshot_cli cleanup <dir> [--keep N]` with **no dry-run, no
> confirmation, and a `--keep 10` default** — pointed at the consolidated archive that deletes
> **27,886 of 27,896** models. Worse, it sorted by `mtime`, which in this archive is *not* creation
> time (a copy reset every timestamp), so "keep the N most recent" did not select what it claimed
> to. And it said `git clean` had "**none** — no structural mitigation", which is also false: a
> nested repo demotes the risk. Both fixed above.

---

## 4. Consequences

### 4.1 Work required — the complete table

Produced from an **untruncated** `--all` sweep across all nine repos for `cascor_snapshots`,
`cascor-snapshots`, `src/snapshots`, `JUNIPER_CASCOR_SNAPSHOTS_DIR`, and `snapshot_history.jsonl`.
The first draft's 12-item table missed 17 references; that is why the sweep now runs *before* the
table is written.

**juniper-cascor (#545)** — 20 files:

| # | target | change |
|---|---|---|
| 1 | `pyproject.toml` | **`namespaces = false`** — the §1.1 structural guard |
| 2 | `src/cascor_constants/constants_hdf5/constants_hdf5.py` | §3.3(b) resolution |
| 3 | `juniper-cascor-model/cascor_constants/constants_hdf5/constants_hdf5.py` | **byte-identical** lockstep edit (drift gate) |
| 4 | `src/api/lifecycle/manager.py::_get_snapshots_dir` | default → `<repo>/cascor-snapshots` |
| 5 | `.gitignore` | `/cascor-snapshots/*` + `!…/.gitkeep`; superseded roots kept ignored; the inert sibling rule retired |
| 6 | `cascor-snapshots/.gitkeep` | **new, tracked** — §4.2 |
| 7 | `scripts/juniper-cascor.service` | one `ReadWritePaths` entry, **`-` prefixed**, all four entries |
| 8 | `Dockerfile` | `ENV JUNIPER_CASCOR_SNAPSHOTS_DIR` + `mkdir` |
| 9 | `.dockerignore` | exclude the artifact roots and `logs/` |
| 10 | `src/snapshots/snapshot_utils.py` | `cleanup_old_files` dry-run default + shared-root refusal |
| 11 | `src/snapshots/snapshot_cli.py` | `--yes` flag, dry-run messaging |
| 12 | `conf/common.conf` | `SNAPSHOTS_DIR_NAME` / `SNAPSHOTS_DIR` — a **third** definition of the root, sourced by `util/script_template.bash` and `util/get_code_stats.bash` |
| 13 | `util/rename_snapshots.bash` | `DEST_DIR` |
| 14 | `src/tests/unit/api/test_w6_snapshots_dir_override.py` | both pinned defaults + 9 new arms |
| 15 | `juniper-cascor-model/tests/test_constants_dir_overrides.py` | pinned leaf name + installed-copy arm |
| 16-19 | `docs/api/API_REFERENCE.md`, `docs/source/QUICK_START.md`, `docs/install/REFERENCE.md`, `notes/API_REFERENCE.md` | artifact-path rows |
| 20 | `CHANGELOG.md` | |

**juniper-deploy (#189)** — 8 files: `docker-compose.yml` (bind mounts + env on both cascor services
and canonical canopy; named volume retired), `scripts/preflight_snapshot_root.sh` (new), `Makefile`,
`k8s/helm/juniper/templates/cascor-deployment.yaml`, `k8s/helm/juniper/values.yaml`,
`docs/REFERENCE.md`, `.env.example`, `CHANGELOG.md`.

**juniper-ml (this PR)** — this document, plus: `util/isolated_stack.bash` (canopy read pointer +
the teardown that must never follow it), `tests/test_isolated_stack_script.py`,
`util/worktree_cleanup.bash` (snapshot guard), `util/ad-hoc/2026-08-16_snapshot_archive_census.py`,
`util/ad-hoc/2026-08-20_shape_broken_network_probe.py`,
`util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash` (`--exclude-dir`), `docs/REFERENCE.md` ×2.

**Deliberately not done** — the inert `**/cascor/cascor_snapshots/*` rule in five sibling repos
(canopy, cascor-client, cascor-worker, data, deploy). It matches nothing (§4.2), and retiring it
would mean five PRs for zero behaviour change. Recorded as hygiene, not scheduled.

### 4.2 The `.gitignore` rule: directory-anchored, and `.gitkeep`-able

Two decisions in one line.

**Directory-anchored, not filename-anchored.** CLI snapshots used to be ignored by *filename*
(`cascor_snapshot_*.h5`) — proven with `git check-ignore --no-index`, which reports a non-conforming
name in the same directory as *not ignored*. The service tier's own `snapshot_<ISO>Z.h5` never
matched at all, which is the sound half of the argument. (The draft's other half — that Phase 6.1's
`run_id` rename would break the rule — was **wrong**: the specified name
`cascor_snapshot_<ISO8601Z>_<run_id|norun>_<uuid8>.h5` still matches `cascor_snapshot_*`.)

**`/cascor-snapshots/*` + `!/cascor-snapshots/.gitkeep`, not the bare directory form.** Git cannot
re-include a path under an excluded directory, and the `.gitkeep` is load-bearing twice:

- systemd **fails** a unit whose `ReadWritePaths=` names a missing path, and under
  `ProtectSystem=strict` + `ProtectHome=read-only` the service could not create it anyway. Both
  entries this replaces lacked the `-` prefix *and* named directories that no longer exist — the
  unit as shipped could not start.
- a missing docker bind-mount source is created by the **daemon, as root**, which then EPERMs the
  uid-1000 container on every save.

Shipping the directory is what makes a fresh clone — the C-3 headline case, a second researcher —
work at all. `logs/*` at the top of the same file already uses this form.

The sibling-repo rule `**/cascor/cascor_snapshots/*` (`/**` in juniper-data and juniper-deploy) is
**inert** in all six repos: it requires a path component named exactly `cascor`, and no repo has one.

### 4.3 Canopy is a reader, and that is in scope

> ⛔ **RETRACTED — the first draft dismissed canopy as "a different repo with a different artifact
> type".** That is true of canopy's own `snapshot_history.jsonl`, and false of the thing that
> matters: **canopy LISTS and resolves cascor's `.h5` by reading a local directory** —
> `JUNIPER_CANOPY_SNAPSHOT_DIR`, else `CASCOR_SNAPSHOT_DIR`, else `./snapshots` relative to its own
> CWD (`juniper-canopy/src/main.py:1713-1725`). None of the three canopy compose services had a
> `volumes:` key, and compose set no snapshot variable, so **the dashboard's snapshot list has always
> been empty in Docker** while cascor held the files. No error, no warning.

Fixed in deploy#189 for the canonical `juniper-canopy`, read-write (canopy appends
`snapshot_history.jsonl` and mkdirs the root) — safely, because canopy has **no delete path**: no
`unlink`, `rmtree`, or `os.remove` anywhere in `src/main.py`. `juniper-canopy-demo` and
`-dev` run `JUNIPER_CANOPY_DEMO_MODE` and are deliberately left unmounted.

On the host, `util/isolated_stack.bash` pointed canopy at `${CASCOR_SRC_DIR}/snapshots`, which
juniper-cascor#537 vacated — so the F-CANOPY-007 remediation was **already broken** before this
ruling. Repointed at the shared root, and its stale "the docker topology co-mounts one volume into
both services" comment corrected.

Still out of scope: whether `juniper-canopy/canopy-snapshots/` should exist per the
`<repo>/<short-repo-name>-snapshots/` naming scheme. Canopy's repo-root `snapshots/` holds one
`snapshot_history.jsonl` and zero `.h5`. **Flagged as follow-up.**

---

## 5. What was rejected, and why it stays rejected

| Option | Why not |
|---|---|
| `~/.local/state/juniper-cascor/snapshots` | C-1/C-2. Outside the backup tree; restore stops being copy+extract; dotfile collision risk for a key project asset. |
| Docker named volume (fixed to the right path) | C-1 and C-5. Invisible to a tree-walking backup; `down -v` and `make clean` destroy it. |
| Per-run `RUN_DIR/snapshots` as the **default** | C-3. Fragments the shared archive. Remains correct as an **override** — `experiment_stack.bash` already does this, and it is the sanctioned way to isolate an experiment. |
| Keep `src/cascor_snapshots/` | C-4, plus the juniper-cascor#501 class. |
| Underscore at repo root | Weaker than the hyphen, though **not** for the reason the first draft gave (§1.1). |
| A divergent package copy with no default | Viable, and cheaper than the draft believed (§3.3). The `sysconfig` test made byte-identity work, so the divergence was not needed — but it was a real option, not the non-starter the draft implied. |

### 5.1 The k8s path is an accepted exception

The Helm chart is a **fourth stack origin** the first draft omitted entirely, and it carried the
identical `/app/data` mount-vs-write-path defect — a 10Gi PVC sat idle while the pod wrote to its
ephemeral layer. deploy#189 fixes the mount.

It cannot satisfy C-1 or C-3: a PVC is invisible to a tree-walking backup, `ReadWriteOnce` cannot be
shared across nodes, and `helm uninstall` destroys it. That is recorded as an **accepted exception**
in `values.yaml` where an operator will read it, on the grounds that transfer to or from a cluster is
out-of-band and user-driven anyway — which is the stated policy for moving snapshots between hosts.

---

## 6. Risks this design accepts

1. **A linked git worktree gets its own root, deliberately.** `<worktree>/cascor-snapshots`, not the
   primary checkout's. Redirecting was considered and **declined**: a test run in a worktree would
   then write into the live 27,896-file archive, and test isolation is worth more than making a
   temporary task checkout a fourth stack origin. Worktrees are a developer context, not a stack
   origin. The real hazard — `git worktree remove` deleting an ignored directory **without**
   `--force`, which `worktree_cleanup.bash` does automatically — is now guarded by refusal.
2. **UID/GID coincidence.** Writable because host and container are both 1000:1000. Elsewhere it
   needs `JUNIPER_UID`/`JUNIPER_GID`-style plumbing (never `${UID}`, §3.2), and under rootless
   Docker the correct value inverts to `0:0`.
3. **`git clean -xdff` deletes the archive.** A cost of satisfying C-1 that the out-of-checkout
   option did not have. The nested-repo mitigation exists and was declined (§3.4).
4. **Two naming schemes share one directory** — `cascor_snapshot_<date>_<uuid4>.h5` (CLI) and
   `snapshot_<ISO>Z.h5` (service). Harmless to the glob-based lookup; Phase 6.1 unifies them.
5. **No cross-process write coordination.** Three origins share one directory with no locking and no
   HDF5 locking configuration. The contract is **one writer per snapshot id; readers may observe a
   partially written file**. Two saves in the same second are handled by `save_snapshot`'s
   collision-suffix loop, which is itself a TOCTOU.
6. **The external backup tool is unverified.** No backup script, config, or manifest exists anywhere
   in the tree, so whether it actually walks `Juniper/`, whether it honours `.gitignore`, and whether
   it preserves uid/gid on restore are all unconfirmed. **Every C-1/C-2 claim rests on it.** This is
   the highest-leverage thing left to verify, and it is an owner question, not a code question.
7. **The 27,896 existing artifacts are not re-verified** by this change. They moved with the
   directory rename and are expected to load unchanged; nothing here revalidates them. (The frozen
   census figure is 27,869 files / 27,863 loadable; the count has grown since.)

---

## 7. Operator notes

Things an operator will hit that the code cannot tell them.

- **Before the first `compose up`**, the host root must exist and be owned by your uid. It ships
  tracked (`cascor-snapshots/.gitkeep`), so a fresh clone has it. If it is ever absent, the daemon
  creates it **root-owned** and the container EPERMs on every save — with the stack reporting
  healthy. `make snapshot-preflight` checks exactly this.
- **`JUNIPER_CASCOR_SNAPSHOTS_HOST_DIR`** is resolved against the **compose project directory**, not
  your shell's CWD. It must be **absolute** for a remote docker context — relative bind sources are
  only supported by a local runtime. A bare name (no `./`) is read as a named volume and fails closed.
- **Rootless Docker inverts the ownership advice**: use `user: "0:0"`, because rootless container
  uid 0 maps to the invoking host user. `user: "1000:1000"` is what breaks it there.
- **SELinux hosts** need `:z` (shared label) on the mount. Never `:Z` — a private label relabels the
  directory to a container-private type and breaks exactly the host-CLI/systemd sharing C-3 requires.
- **Docker Desktop / macOS / WSL2**: HDF5's default file locking is unreliable over the VM filesystem
  bridge; set `HDF5_USE_FILE_LOCKING=FALSE` and keep the checkout off `/mnt/<drive>`.
- **What `down -v` does and does not destroy after this change**: it destroys `juniper-cascor-logs`
  and `grafana-data`. It does **not** touch snapshots. That is the point of the change.
- **`git clean -xdff` will delete the archive.** `-xdf` will not (the directory is ignored, but
  `-xdf` still removes ignored directories — verify before running either).
- **Restore from the offline archive** preserves *contents*; whether it preserves *uid/gid* depends
  on the archiver and on whether the restore runs as root. After extracting, confirm the root is not
  root-owned and that `JUNIPER_CASCOR_SNAPSHOTS_DIR` still points at it.
- **Env-var map** — four spellings in this space, deliberately listed together:

  | variable | read by | default |
  |---|---|---|
  | `JUNIPER_CASCOR_SNAPSHOTS_DIR` | cascor CLI (import-time) + service (call-time) | `<repo>/cascor-snapshots` |
  | `JUNIPER_CANOPY_SNAPSHOT_DIR` (**singular**) | canopy list/resolve | `./snapshots` (CWD-relative) |
  | `CASCOR_SNAPSHOT_DIR` | canopy, **deprecated** | — |
  | `JUNIPER_CASCOR_SNAPSHOTS_HOST_DIR` | compose only, host side of the bind | `../juniper-cascor/cascor-snapshots` |

---

## 8. Verification

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper

# The packaging guard — use the NAMESPACE finder; plain find_packages is not what setuptools runs.
cd "$JUNIPER/juniper-cascor" && python -c "
import tomllib, pathlib
from setuptools.config import expand
f = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['tool']['setuptools']['packages']['find']
tops = {p.split('.')[0] for p in expand.find_packages(where=f['where'], exclude=f['exclude'],
                                                     namespaces=f.get('namespaces', True), root_dir='.')}
print('snapshot dirs:', [t for t in tops if 'snapshot' in t])
print('sibling dists:', [t for t in tops if t.startswith('juniper-')])"

# The ignore rule: artifacts out, .gitkeep in
git -C "$JUNIPER/juniper-cascor" check-ignore -v --no-index cascor-snapshots/anything.h5
git -C "$JUNIPER/juniper-cascor" add -A -n cascor-snapshots/     # -> only .gitkeep

# The compose bind source actually resolves where you think
cd "$JUNIPER/juniper-deploy" && docker compose --profile full config | grep -A2 'cascor-snapshots'
make snapshot-preflight

# Container and host uid/gid agree
grep -n "useradd --uid\|^USER" "$JUNIPER/juniper-cascor/Dockerfile"; id -u; id -g

# The deleter refuses the shared root
cd "$JUNIPER/juniper-cascor/src" && python -c "
import sys; sys.path.insert(0, '.')
from snapshots.snapshot_utils import HDF5Utils
print(HDF5Utils.cleanup_old_files('../cascor-snapshots', 0, dry_run=False))"   # -> 0, refuses

# Full untruncated reference sweep — run this BEFORE writing any work table
"$JUNIPER/juniper-ml/util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash" --all \
  'cascor_snapshots|cascor-snapshots|JUNIPER_CASCOR_SNAPSHOTS_DIR'
```

---

## 9. Related

- [`JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-ROOT-LOCATION-DECISION-BRIEF.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-ROOT-LOCATION-DECISION-BRIEF.md)
  — the S-1 options analysis this ruling resolves (juniper-ml#1197).
- [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)
  — F-P1-4 design of record; §6.1 identity is the next phase and depended on this ruling.
- juniper-cascor#545 (implementation), #544 (47 tracked artifacts removed), #542 (D-B error
  taxonomy), #537 (service root out of the package), #501 (the module-deletion class).
- juniper-deploy#189 (bind mounts, preflight, Helm).
