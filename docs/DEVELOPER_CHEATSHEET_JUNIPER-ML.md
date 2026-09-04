# Developer Cheatsheet — juniper-ml

**Version**: 1.0.56
**Date**: 2026-09-04
**Project**: juniper-ml

---

## Common Commands

| Command                                                | Description                                     |
|--------------------------------------------------------|-------------------------------------------------|
| `pip install -e ".[all]"`                              | Install meta-package with all extras (editable; multi-GB — pulls torch via `[worker]`) |
| `pip install -e ".[clients]"`                          | Install just the HTTP/WS client libraries (editable) |
| `pip install -e ".[worker]"`                           | Install just the distributed training worker (editable) |
| `pip install -e ".[servers]"`                          | Install just the service distributions: canopy + cascor + data (editable) |
| `pip install -e ".[tools]"`                            | Install shared tooling: ci/doc/config tools + model-core + observability + service-core (editable) |
| `pip install -e ".[recurrence]"`                       | Install Δt-native recurrence stack: model + FastAPI app + HTTP client (editable) |
| `python -m build && twine check dist/*`                | Build and validate package                      |
| `python3 -m unittest -v tests/test_wake_the_claude.py` | Run launcher regression tests                   |
| `python3 -m unittest -v tests/test_pyproject_extras.py`| Lint extras schema + docs↔pyproject pin lockstep |
| `python3 -m unittest -v tests/test_publish_testpypi_verify.py` | Gate 1 two-phase verify + bounded TestPyPI poll (no `sleep 30`) |
| `python3 -m unittest -v tests/test_publish_release_only_trigger.py` | All `publish*.yml` stay `release: published` only (no `push:`) |
| `bash scripts/test_resume_file_safety.bash`            | Run resume file safety regression               |
| `pre-commit run --all-files`                           | Run all pre-commit hooks                        |
| `juniper-check-doc-links --cross-repo skip`            | Validate doc links (CI-parity mode; install via `pip install juniper-doc-tools`) |
| `util/juniper_plant_all.bash`                          | Start the host-level Juniper stack with health gates |
| `util/get_cascor_status.bash`                          | Query host-mode cascor status (`CASCOR_HOST` / `CASCOR_PORT`, default `localhost:8201`) |
| `util/juniper_chop_all.bash`                           | Stop the host-level stack from `JuniperProject.pid` |
| `util/juniper_plant_all.bash --systemd`                | Start via `systemctl --user` (no pidfile; curl required) |
| `util/juniper_chop_all.bash --systemd`                 | Stop via `systemctl --user` (reverse order; soft-fail; no pidfile path) |
| `util/install_duplicati_timer.bash`                    | Install (copy, not symlink) the `systemd --user` Duplicati backup lane; does **not** enable the timer |
| `systemctl --user enable --now duplicati-backup.timer` | Enable the overnight timer **after** a first full backup and a restore drill |
| `systemctl --user list-timers duplicati-backup.timer`  | Confirm the next `duplicati-backup.timer` fire time |
| `util/experiment_stack.bash --dry-run --up --cascor`   | Preview a per-run experiment stack (ports 8110–8289; no side effects) |
| `util/experiment_stack.bash --up --cascor --config PATH` | Bring up data+cascor for one experiment run (`--recurrence` for LMU) |
| `python util/experiments/run_experiment.py --config PATH --run-dir RUN_DIR` | Drive one YAML against the run's `ports.json` (plots + stats + manifest) |
| `util/experiment_stack.bash --down RUN_ID`             | Tear down a run (pidfile-first; keeps `artifacts/`) |
| `python util/agent_suite_doctor.py --json`             | Custom-agent suite health check (OK/WARN/FAIL; discovery fail-closed) |
| `python util/fleet_triage/predict_merge.py --pr N --json` | Predicted-merge triage for one open PR (detached clone; never pushes) |
| `python util/fleet_triage/predict_merge.py --batch --json` | Batch triage + same-file cluster map + heal-first merge order |
| `juniper-symbol-loss-check --base ORIGIN --head HEAD` | AST symbol-loss screen (same CLI as `main-verify`) |
| `util/reap_pytest_orphans.bash --dry-run`              | List orphaned Juniper pytest multiprocessing children (no kill) |
| `python3 util/ad-hoc/cascor_freeze_tell.py`            | Cascor-primary freeze tell (exit 1 = in force; 0 ≠ no importer) |
| `python util/env_floor_drift_check.py --repo-root PATH --env NAME` | Floor-drift: installed `juniper-*` vs pyproject floors (I-2) |
| `python util/fleet_triage/predict_merge.py --pr N --json` | Predicted-merge triage for one open PR (detached clone; never pushes) |
| `python util/fleet_triage/predict_merge.py --batch --json` | Batch triage + same-file cluster map + merge order |
| `python util/snapshot_attribute.py --null-only` | Print per-dataset untrained floors (no sidecar write) |
| `python util/snapshot_attribute.py --sample 300 --seed 4242 --json` | Sampled attribution probe (`--seed` samples snapshots, **not** generators) |
| `python3 -m unittest -v tests/test_snapshot_attribute.py` | Attribution regressions incl. dataset-instance pin (#1333) |
| `./claudey`                                            | Launch default interactive Claude session       |

**Cascor-primary freeze:** `python3 util/ad-hoc/cascor_freeze_tell.py`. Exit 1 = a user-owned process holds `/home/pcalnon/Development/python/Juniper/juniper-cascor` — do not edit it. Exit 0 is "no user-owned importer", not "no importer" (root-owned `/proc/<pid>/{fd,environ,maps}` are invisible). Sibling `juniper-cascor-client` / `-worker` and both worktree roots are not holds. [REFERENCE.md § Cascor Primary Freeze Tell](REFERENCE.md#cascor-primary-freeze-tell).

---

## Secrets Management (SOPS)

> See: `notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md`

| Task            | Command                                                            |
|-----------------|--------------------------------------------------------------------|
| View secrets    | `sops -d --input-type dotenv --output-type dotenv .env.enc`        |
| Decrypt to file | `sops -d --input-type dotenv --output-type dotenv .env.enc > .env` |
| Re-encrypt      | `sops -e --input-type dotenv --output-type dotenv .env > .env.enc` |

**Add/change:** Decrypt, edit `.env`, re-encrypt, commit `.env.enc`. If Docker-consumed, also update `juniper-deploy/.env.example`.

**Remove:** Decrypt, delete the key, re-encrypt. Remove references in code, `docker-compose.yml`, `.env.example`.

**Add SOPS to a new repo:** Copy `.sops.yaml`, create and encrypt `.env`, add `no-unencrypted-env` hook, ensure `.env` in `.gitignore`.

**Rotate age key:** `age-keygen` new key, update `~/.config/sops/age/keys.txt`, update `.sops.yaml` in all 8 repos, re-encrypt all `.env.enc`, update `SOPS_AGE_KEY` GitHub Actions secret per repo.

---

## Claude Code Session Script

> See: `scripts/wake_the_claude.bash` | `scripts/default_interactive_session_claude_code.bash`

| Entry Point                             | Behavior                                                      |
|-----------------------------------------|---------------------------------------------------------------|
| `./claudey`                             | Default interactive session (`--id --worktree --effort high`) |
| `./claudey --prompt "..."`              | Custom prompt, default flags                                  |
| `CLAUDE_SKIP_PERMISSIONS=1 ./claudey`   | Adds `--dangerously-skip-permissions`                         |
| `bash scripts/wake_the_claude.bash ...` | Direct launcher with full flag control                        |

The wrapper does **not** include `--dangerously-skip-permissions` unless `CLAUDE_SKIP_PERMISSIONS=1` is set.

**Interactive** (default): runs `claude` in foreground. **Headless**: add `--print` to launch via `nohup`, logs to `logs/wake_the_claude.nohup.log` (fallback: `$HOME/`).

### Session ID and Resume

```bash
bash scripts/wake_the_claude.bash --id --prompt "hello"                                      # generate session ID
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "..." # resume by UUID
bash scripts/wake_the_claude.bash --resume session-id.txt --prompt "..."                       # resume by file
```

**Safety:** `--id` refuses symlink targets. Resume filenames must be `.txt` basenames (no `/`). File contents must be a valid UUID. Invalid/missing files are preserved.

**Known pitfall:** `claude` is invoked with unquoted `${CLAUDE_CODE_PARAMS[@]}`; prompt strings may split on spaces. Run regression tests after changes.

### Resume And Fork Alias Forwarding

`scripts/wake_the_claude.bash` accepts multiple alias flags, but always forwards canonical Claude CLI flags:

| Input Alias Family | Accepted Aliases | Forwarded Canonical Flag |
|--------------------|------------------|--------------------------|
| Resume             | `-r`, `--resume`, `--resume-thread`, `--resume-session` | `--resume` |
| Fork session       | `--fork`, `--fork-session`, `--resume-fork`, `--resume-fork_session` | `--fork-session` |

Example (alias input to canonical output):

```bash
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --fork --prompt "hello"
# Forwards args to claude as: --resume <uuid> --fork-session "hello"
```

This behavior is regression-tested in `tests/test_wake_the_claude.py`:
- `test_resume_alias_flag_passes_session_id_to_claude`
- `test_fork_session_alias_forwards_canonical_flag`

| Resume Symptom                  | Cause                                | Fix                                                      |
|---------------------------------|--------------------------------------|----------------------------------------------------------|
| `Session ID is invalid`         | Bad UUID or file content             | Verify UUID format                                       |
| `no Valid Session ID to Resume` | Missing value after `--resume`       | Provide UUID or `.txt` basename                          |
| File resume fails immediately   | Path separator, wrong ext, wrong dir | Use basename `*.txt` in `scripts/sessions/`              |
| Alias not recognized            | Parsing regression                   | Run `python3 -m unittest -v tests/test_wake_the_claude.py`, verify alias lists and canonical forwarding |

---

## Dependencies

1. **Add**: Edit `pyproject.toml`, regenerate lockfile (`uv pip compile pyproject.toml --extra all -o requirements.lock`), install
2. **Remove**: Delete from `pyproject.toml`, remove imports, regenerate lockfile, run tests
3. **Edit optional group / pin**: Update `[project.optional-dependencies]` in `pyproject.toml` and co-update in the **same PR** (two CI gates):
   - `tests/test_pyproject_extras.py` `EXPECTED_EXTRAS` (`PyprojectExtrasTest` — pin-string / schema drift fails Regression Tests; Dependabot-only bumps cannot update it — juniper-ml#905)
   - Documented extras tables: `AGENTS.md`, `README.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md` (`ExtrasDocsLockstepTest` — pin strings must match `pyproject.toml` **exactly**; juniper-ml#907)
   - When adding a new extra, include it in `[all]` (except the `[doc-tools]` alias, already covered by `[tools]`)
4. **Verify**: `python3 -m unittest -v tests/test_pyproject_extras.py` (covers both gates once #907 lands)

> Tip: Inline extras tables must keep the **full** pin in backticks (`juniper-foo>=X,<Y`). Stale `tools` ceilings (`model-core` / `service-core`) and omitted REFERENCE rows are the drift class #906 synced; after #907 merges, `ExtrasDocsLockstepTest` fails CI on that class. Current truth: `juniper-model-core>=0.1.0,<0.4.0`, `juniper-service-core>=0.2.0,<0.8.0`.
> See: per-repo `pyproject.toml` | `juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md` | [REFERENCE.md § Extras Reference](REFERENCE.md#extras-reference)

### Cross-Repo Version Sync

1. Create worktrees in each affected repo with consistent branch prefix (e.g., `chore/bump-pydantic`)
2. Update `pyproject.toml` and regenerate lockfiles per repo
3. Test and merge in dependency order: libraries (`data-client`, `cascor-client`) before services (`cascor`, `canopy`)

### Release Coordination

1. Bump version in `pyproject.toml`, create GitHub Release (`vX.Y.Z` tag) -- publishes via OIDC to TestPyPI then PyPI
2. Update downstream `pyproject.toml` minimum version pins after publish
3. For juniper-ml: update extra version pins, release new meta-package version
4. Merge order: data-client, cascor-client, cascor-worker, then juniper-ml

### juniper-observability Release

`juniper-observability` is a subpackage in this repository with its own CI and publish lifecycle.

| Task | Command / Procedure |
|------|---------------------|
| Local package tests | `cd juniper-observability && python -m pytest --cov=juniper_observability --cov-report=term-missing --cov-fail-under=90` |
| Local build check | `cd juniper-observability && python -m build --sdist --wheel && twine check dist/*` |
| Publish | Cut a GitHub Release with tag `juniper-observability-vX.Y.Z` (never a bare `git push <tag>`) to trigger `.github/workflows/publish-observability.yml` |
| Retry publish | Use `workflow_dispatch` on `.github/workflows/publish-observability.yml` against the existing tag |

Publish flow: build uploads `juniper-observability-dist` for seven days, TestPyPI downloads and publishes it with OIDC, TestPyPI `--no-deps` install is retried 5×10s for index lag, then PyPI downloads the same artifact after TestPyPI verification succeeds.

Constraint: publish jobs currently run on GitHub-hosted `ubuntu-latest` runners with SHA-pinned artifact actions. If switching to self-hosted runners, verify compatibility with the pinned `actions/upload-artifact` and `actions/download-artifact` versions before tagging a release.

---

## Git Worktrees

> See: `notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md` | `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`

**Create:** From repo root on clean `main`, create branch, then:

```bash
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}--${SAFE_BRANCH}--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME" && cd "$WORKTREE_DIR"
```

**Clean up (V2 -- PR workflow):**

1. Push: `cd "$OLD_WORKTREE_DIR" && git push origin "$OLD_BRANCH"`
2. New worktree BEFORE removing old: `git worktree add "$NEW_DIR" -b "$NEW_BRANCH" origin/main && cd "$NEW_DIR"`
3. PR (not direct merge): `gh pr create --base main --head "$OLD_BRANCH" --title "..." --body "..."`
4. After merge: `git worktree remove "$OLD_WORKTREE_DIR" && git branch -d "$OLD_BRANCH" && git worktree prune`

**Automated**: `util/worktree_cleanup.bash --old-worktree "$DIR" --old-branch "$BRANCH" --parent-branch main`

**Phase 1 dirty gate:** Live cleanup hard-fails (`exit 1`, `Commit or stash changes before running cleanup`) when `git status --porcelain` in the old worktree is non-empty — it never reaches `git push`.
`--dry-run` skips the porcelain check (always pretends clean). Commit or stash, then re-run.
See procedure V2 § "Phase 1 dirty-tree + push gates (script)".

**Phase 3 PR reuse / non-main parent (juniper-ml#759):** if `gh pr list` already finds an open PR for the head Phase 3 would open, the script logs `PR #<n> already exists` and never calls `gh pr create`.
With `--parent-branch` ≠ `main`, Phase 3 merges the feature into the parent, pushes the parent, then opens `parent → main` (not `feature → main`).
Dry-run previews that merge/push/PR sequence. Full table: cleanup procedure V2 § "PR Already Exists for Branch (script Phase 3)".

**Phase 4 remote delete:** Prefer `--skip-remote-delete` when a PR is still open (never calls `gh`).
Without the flag, the live path auto-skips `push --delete` if `gh pr list --repo pcalnon/juniper-ml --head "$OLD_BRANCH" --state open` returns a positive length **or** if the `gh` query fails / returns a non-numeric result (fail-closed; juniper-ml#739).
Local worktree + local branch are still removed. Hard-wired to `juniper-ml` — use the flag for sibling-repo cleanups.
See procedure V2 § "Phase 4 remote-branch deletion (script)".

**Batch stale sweep** (centralized `…/Juniper/worktrees/` pool): survey → dry-run apply → apply. Survey treats gitignored debris as clean; apply still skips ignored-only `SAFE` rows unless you pass `--include-ignored` after review (decrypted-secrets class). Full contract: cleanup procedure V2 § "Batch Stale-Worktree Sweep".

```bash
bash util/ad-hoc/worktree_sweep_survey.bash > /tmp/juniper-worktree-sweep.tsv
bash util/ad-hoc/worktree_sweep_apply.bash --dry-run < /tmp/juniper-worktree-sweep.tsv
bash util/ad-hoc/worktree_sweep_apply.bash --include-ignored < /tmp/juniper-worktree-sweep.tsv
```

---

## Data Contract

NPZ format: keys `X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full` (all `float32`).

```python
from juniper_data_client import JuniperDataClient
client = JuniperDataClient(base_url="http://localhost:8100")
dataset_id = client.create_dataset("spiral", {"n_points": 200, "noise": 0.1})
npz = client.download_artifact_npz(dataset_id)
```

Generators: `spiral`, `xor`, `gaussian`, `circles`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`

REST `base_url` (data / cascor / recurrence HTTP clients on GitHub main): strip, case-insensitive `http(s)://` default, require `hostname` (not `netloc`), drop trailing `/` and `/v1`. Hostless values raise `Juniper*ConfigurationError` at init. Cascor WS streams (`CascorTrainingStream` / `CascorControlStream`) and `FakeCascorClient` stay `rstrip("/")` only. Extras floors do not yet require the new wheels — see [REFERENCE — HTTP Client Base-URL](REFERENCE.md#http-client-base-url-contract).

---

## CI/CD

| Task                   | Command / Procedure                                                                         |
|------------------------|---------------------------------------------------------------------------------------------|
| Pre-commit             | `pre-commit run --all-files`                                                                |
| Fleet predicted-merge  | `python util/fleet_triage/predict_merge.py --pr N` / `--batch` (exit 0 = report; 2 = misuse) |
| Pre-commit (PR scope)  | `pre-commit run --from-ref <BASE> --to-ref HEAD` (matches `ci.yml` G4 on PR / merge_group)  |
| Sequence-safety (local)| `juniper-symbol-loss-check --base origin/main --head HEAD` (+ docs sibling) |
| Post-merge main-verify | Auto on every `push:main` (`.github/workflows/main-verify.yml`); see tip below              |
| Publish `juniper-ml`   | Create GitHub Release with `vX.Y.Z` tag (OIDC; Gate 1 = three TestPyPI installs)            |
| Publish shared package | Create GitHub Release with a `juniper-<pkg>-vX.Y.Z` tag → `publish-<pkg>.yml` (six packages)|
| Retry shared publish   | `gh workflow run publish-<pkg>.yml --repo pcalnon/juniper-ml --ref juniper-<pkg>-vX.Y.Z`    |
| Weekly security scan   | Actions → Scheduled Security Scan (`pip-audit --strict --desc on` after `pip install -e .`) |
| CodeQL Analysis        | `.github/workflows/codeql.yml` — required context `Analyze (python)`; see tip below         |
| Weekly lockfile refresh| Actions → Update Lockfiles (`juniper-generate-dep-docs` → PR on `chore/lockfile-update`)    |
| Weekly docs-full-check | Mon 06:00 UTC / dispatch — clones `ECOSYSTEM_REPOS`, `--cross-repo check` + pin screens     |
| Audit this `claude.yml`| `bash util/validate_claude_yaml_access.bash .github/workflows/claude.yml`                   |
| Live `@claude` assistant | `.github/workflows/claude.yml` — SHA-pinned `anthropics/claude-code-action`; not a required check; see tip below |
| Audit all siblings     | `JUNIPER_ROOT=/path/to/Juniper bash util/validate_claude_yaml_access.bash`                  |
| AGENTS.md date bump    | **You bump it**; CI verifies on PRs touching `AGENTS.md` (`agents-md-touch-up.yml`; no bot commit) |
| Shared-package CI      | Path-scoped `ci-<pkg>.yml` under `.github/workflows/` (six packages; see REFERENCE)         |
| Open-PR budget alarm   | Daily 14:00 UTC `pr-budget-alarm.yml` (report-only); `gh workflow run pr-budget-alarm.yml`  |
| Doc links (CI parity)  | `juniper-check-doc-links --exclude templates --exclude history --exclude legacy --cross-repo skip` |
| Doc links (full local) | `juniper-check-doc-links --cross-repo check`                                                |
| Re-run main-verify     | `gh workflow run main-verify.yml --repo pcalnon/juniper-ml` (dispatch; catch-up BASE still applies) |
| Sequence-safety (local) | `juniper-symbol-loss-check --base origin/main --head HEAD` (+ sibling `docs_additions_check.py`) |
| Fleet predicted-merge  | `python util/fleet_triage/predict_merge.py --pr N` / `--batch` (exit 0 = report; 2 = misuse) |

Key hooks: `ruff` (juniper-data) or `black`+`isort`+`flake8` (others), `mypy`, `bandit`, `shellcheck`, `no-unencrypted-env`.

**Sequence-safety / fleet triage (juniper-ml#895 / #908 / #910 / #926):** `predict_merge` shells out
to `juniper-symbol-loss-check (juniper-ci-tools)` on the merged RESULT (byte-identical to post-merge
`main-verify`; fail-soft: checker `skip` ≠ damage). The inline docs screen counts removed content `-`
lines on changed `.md` only (ignores the `---` header) and honors `Allow-Docs-Rewrite` trailers
(path / basename / `*`). Intentional symbol removals need an `Allow-Symbol-Loss: <qualified.symbol>`
commit trailer in BASE..HEAD — the per-PR `allow-symbol-loss` label is WARN-only advisory and does
**not** green `main-verify`. Docs-only deltas skip the pre-commit battery (`no .py files in delta`).
`--batch` orders heal titles/branches first (`restore` / `heal` / `repair` / `fix-first`). Verdicts:
`NEEDS-UPDATE-BRANCH` means behind-main; `DAMAGED-FIX-FIRST` is gate **or** symbol **or** docs `fail`.
Skip local pre-commit with `JUNIPER_FLEET_SKIP_PRECOMMIT=1`. Full contract:
[REFERENCE.md § Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety).

Meta-package publish flow: build + `twine check`, TestPyPI upload with attestations, TestPyPI install verification, then PyPI upload.

`juniper-observability` publish flow: build from `juniper-observability/`, TestPyPI upload with `verbose: true`, retry install verification to tolerate index lag, then PyPI upload. The workflow reads the version from `juniper-observability/pyproject.toml`; keep it aligned with `juniper-observability/juniper_observability/_version.py`.

**Static-package version lockstep (ml#701):** all five in-repo static packages (ci-tools, config-tools, doc-tools, observability, service-core) also ship `<import>/_version.py`.
Hand-bumps and release-train proposals must move `[project].version` and `__version__` together — a pyproject-only bump ships a wheel whose `__version__` lies.
Always-on gate: `tests/test_release_train_registry.py` (`VersionDunderLockstepTest`).

`propose.py` emits the dunder co-change automatically (juniper-ml#710).
If `__version__` is already at the proposed version (re-entry / partial heal), step 3a stays silent instead of false-flagging REQUIRED (juniper-ml#712).
Gate 1 review table: release-train operator runbook §3.2.

**Re-entry caveat (juniper-ml#712):** if `__version__` already equals the proposed version, the train leaves the dunder alone and does **not** checklist REQUIRED-manual. Confirm the match before treating a pyproject-only proposal as the old failure class.

**Sibling / meta AGENTS.md Version (worker#140 / ml#706 / #720):** when hand-bumping a sibling repo's
**primary** package (`pypi_name` equals the repo name) or the meta-package, move `AGENTS.md`
`**Version**:` with the version file — CI embeds the portable `test_agents_md_version_drift` lint.
Release-train `propose.py` steps 5/5a do this automatically; already-at-target is silent success
(no false `REQUIRED`); absent / missing-header surfaces `REQUIRED` (never invents). Sub-packages
hosted in a sibling never touch the host header.

**Propose CHANGELOG refuse clears staged edits (juniper-ml#751):** `build_proposal` stages the version
(and optional dunder) bump before the CHANGELOG move. Empty / missing Unreleased or a missing CHANGELOG
clears those edits so the skipped stub is `edits=[]` + `skipped_reason` (same shape as dup-guard /
`bump=none`) — do not treat leftover version edits in dry-run JSON as a Gate 1 candidate.
Operator table: release-train runbook §3.2.

**Release-train detect / ceremony edges (monitor `NOT_FOUND`, SHIP filter, SemVer).** Ceremony
`monitor_publish_run` keeps polling when the publish run is briefly invisible (`NOT_FOUND`); a
timeout while still building *or* permanently missing reports honest `IN_PROGRESS` (never invents
`PENDING` / `RELEASED` / HALT) — re-run ceremony after confirming the publish workflow fired.
Detector SemVer: Keep-a-Changelog `Security` → patch, `Changed` → minor; `local_git_compare` treats
`.py` A/D/R/**C** as inherently substantive. Live `gh compare` at the **300-file** cap falls back to
`local_git_compare` and **keeps remote commit first-lines** for SemVer (`detect.py:368-371`; pin
juniper-ml#729). Operator tables:
[`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.1 / §3.3.

**Daily detect `SHIP_UNCERTAIN` / hygiene:** `SHIP_UNCERTAIN` means the detector could not prove ship or
no-ship (missing declared version, missing tag, soft-fail compare, 300-file truncated empty window, or
uncertain hunks) — it is an action classification (exit 1), never a silent `UP_TO_DATE`.
Hygiene `TAG_ONLY=` counts only truthy `tag_only`; a `list_releases` blip sets `tag_only=None` and notes
`release-hygiene (tag_only) unavailable:` without failing the job. Offline `--local-git` must raise
`SourceError` for releases (open [#773](https://github.com/pcalnon/juniper-ml/pull/773)), not return
`set()` (false TAG_ONLY on every package). Operator tables: runbook §3.1.

**Release-train `packages` dispatch + `--cross-repo`.** Both write jobs reject garbage
`packages` tokens (`Juniper-Observability`, underscores, `../`, `;`) with exit **2** + `::error::`
before python runs; empty = all eligible; commas ≡ whitespace. `--cross-repo` only when `APP_TOKEN`
is non-empty. Runbook §3.2; pin juniper-ml#729 `PackagesInputRehearsalTest`.


**Release-train propose step summary:** after `mode=propose`, read the job step summary — it buckets
`propose.py`'s `opened:` / `skip:` lines into Opened / Skipped sections. An empty `propose-output.txt`
shows `produced no output` (crash); a non-empty no-op shows `0` / `0` without that banner. Detail:
runbook §3.2. Hermetic pin: juniper-ml#730 (`ProposeSummaryRehearsalTest`).


**Release-train ceremony archive reuse:** re-dispatching `ceremony` while an exempt notes-archive PR is
still open reuses it (no duplicate open; `--auto` arms on the archive **branch**). If the notes file is
already on `main`, ceremony cuts the Release only (no archive-PR / auto-merge calls). Do not close a
healthy open archive PR to "start over". Detail: runbook §3.3 / §5.5. Hermetic pin: juniper-ml#730.


**Release-train write-job git identity (ml#705):** when editing `.github/workflows/release-train.yml`, keep both `propose` and `ceremony` identity steps on `git config --global user.name|user.email|commit.gpgsign` (never bare repo-local `git config`). Cross-repo commits land in freshly-cloned sibling checkouts; a juniper-ml-only identity leaves them with `Author identity unknown` (run 30040138774). Operator detail: runbook §7 / §8.7.

**Release-train propose skips / Gate 2 park (juniper-ml#749):** `build_proposal` refusal stubs (`bump=none`, unreadable/unparseable version, empty/missing Unreleased, missing CHANGELOG) set `skipped_reason` and open no PR — never invent a bump or empty section.
Detect discounts `tests/` / `test_*.py` / `conftest.py` / `*_test.py` as nonship before the hunk filter (test-only tips stay out of Gate 1).
Ceremony `PENDING_PYPI_APPROVAL` also parks when TestPyPI succeeded and the pypi job is `queued` / `pending` / `""` (run may still be `in_progress`).
Operator tables: release-train runbook §3.2 (refusals + test-path) and §3.3 (job-level park).

**Release-train propose registry miss / execute seams (juniper-ml#764):** a proposable manifest package
absent from `registry.yaml` becomes a skip stub (`skipped_reason="package not in registry.yaml"`) —
the propose job does not crash mid-loop. `--execute` hard-fails (exit 2) if the write/git/pr seam is
missing; skipped or branchless proposals issue zero write calls. Ceremony's parallel for
`BUMPED_NOT_RELEASED` is the `not-in-registry` HALT. Operator table: release-train runbook §3.2.

**Gate 1 notes draft (`notes_render`, coverage juniper-ml#756):** meta-package title must read `# Juniper ML v…` (not `# juniper-ml v…`);
`Release Type` maps `major`→MAJOR / `minor`→MINOR / `patch|none|unknown`→PATCH;
`Breaking changes` is YES only when Unreleased has a `Removed` category;
Keep-a-Changelog accepts `*` as well as `-` (continuations fold).
Operator table: release-train runbook §3.2.

**`link_base` CHANGELOG rewrite (juniper-ml#877):** ceremony archives use the owning repo's tag-pinned
`blob/<tag>` URL; propose drafts use `blob/main`. Relative `[text](docs/…)` / `[text](notes/…)` links
become absolute so centrally archived notes under `notes/releases/` do not 404 (canopy v0.6.0 class).
Absolute / `mailto:` / `#anchor` / `//…` links stay untouched; omit `--link-base` → no rewrite.
Operator table: release-train runbook §3.2.

**Phase 4.2 propose ordering + follow-ons.** Empty `packages=` propose runs process eligible packages
**upstream-first** (registry `depends_on` DAG). A pre-1.0 MINOR/MAJOR that escapes a consumer
`<next-minor` ceiling also opens a separate standard-gated PR
`deps/<upstream>-ceiling-<new-ceiling>` in the **consumer** repo (pin ceiling only; never on the
exempt archive path). Meta (`juniper-ml`) never gets a follow-on. Operator table:
[release-train runbook](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.2
“Phase 4.2”.

**Ceremony signed-archive failure edges (ml#709 / #714):** if a `ceremony` run dies inside
`open_archive_pr`, do **not** invent a base sha or hand-push an archive branch. Unresolvable
`origin/<base>`, non-422 refs errors (e.g. HTTP 401), and unresolvable existing tips are hard stops;
only tip-at-base or single-commit-atop-base are safe re-entry shapes. Operator table:
[`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.3.

**Ceremony monitor: `HALT_TESTPYPI` vs `HALT_PUBLISH`.** TestPyPI job failure → `HALT_TESTPYPI` and a
`testpypi-verify-failed` dedup issue. A later run `failure`/`cancelled`/`timed_out` (TestPyPI already
green) → `HALT_PUBLISH` with a note only — **no** GitHub issue. Open the publish run; do not wait for
an issue. Details: operator runbook §4.1.

**Ceremony re-entry (`RESUME_MONITOR`).** If a Release tag already exists, re-dispatching
`mode=ceremony` only monitors the publish run — it does **not** re-open the archive PR or re-cut the
Release. Step summary shows **resume-monitor**; `plan_state` stays `RESUME_MONITOR` while `state` is
the monitor verdict. TestPyPI failure on resume still HALTs + files an issue (no re-cut). Distinct from
`ALREADY_RELEASED` (PyPI already serves the target). Operator details: runbook §3.3 / §5.5.

**Ceremony `notes-render-failed` + execute `RELEASED` (juniper-ml#741).** Missing/unreadable
`notes/templates/TEMPLATE_RELEASE_NOTES.md` (or the security template) → §8 HALT
`notes-render-failed` (restore template, re-run; never invent archive body). Publish run
`completed`+`success` → execute final state `RELEASED` (both gates done; no halt issue) — not
plan-time `ALREADY_RELEASED`. Runbook §3.3 / §4.

**Archive-guard FAIL triage:** the exempt notes-archive PR's required check (`Release-Train Archive Guard`)
PASSes only on pure `A` adds under `notes/releases/RELEASE_NOTES_*.md`.
Rename-OUT, Copy (`C`), and Typechange (`T`) are still archive PRs (`touches_releases` checks both rename/copy paths) and FAIL — they never SKIP.
A FAIL drops the PR back to the standard owner gate (no auto-merge).
Operator tables: [`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.3.

**R7 archive-lane `ref=` (juniper-ml#770):** a ceremony `SeamViolation` with `ref=None` / `ref=''` means
the `git/refs` POST omitted a heads ref — fail-closed code bug, not an auth blip. Do not hand-POST a
ref. Re-dispatch after #770; see runbook §7.

**Sequence-safety / fleet triage (juniper-ml#895 / #926):** `predict_merge` shells out to
`juniper-symbol-loss-check (juniper-ci-tools)` on the merge RESULT. Its docs screen stays a stricter
any-removed-line counter (not heading/`--min-run`), but honors `Allow-Docs-Rewrite: <path>` / `*`
trailers like `docs_additions_check.py` so intentional docs rewrites are not forever
`DAMAGED-FIX-FIRST`. `Allow-Symbol-Loss: *` is still rejected. Exit `0` always emits a report —
read each `verdict`. Full contract:
[REFERENCE.md § Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety).

**Post-merge main-verify (G3 / G3.1 / notify 0.3.0):** every `push:main` runs
`.github/workflows/main-verify.yml` (per-SHA concurrency, never cancelled). `symbol-screen` always
runs the sequence-safety CLIs; `battery` is path-gated (`tests/` \| `util/` \| `scripts/` \|
`.github/` \| `pyproject.toml`). On failure, `notify` upserts **one** open issue titled
`main-verify: post-merge verification failing` (later failing SHAs comment on it; not auto-closed on
green — owner closes after adjudication) plus non-blocking Slack. G3.1 BASE = last successful
main-verify tip when it is an ancestor of HEAD (sweeps `[skip ci]` gaps), else `event.before`, else
`HEAD^1`. PR labels `allow-symbol-loss` / `docs-rewrite` do **not** green post-merge — use
`Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` commit trailers. Keep the battery list in lockstep with
`ci.yml`'s `tests` job. Full contract: [REFERENCE — Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification).

**CodeQL Analysis (`Analyze (python)`):** `.github/workflows/codeql.yml` is Python semantic SAST
(`queries: +security-and-quality`). The check is a **ruleset** required context, not a Quality Gate
`needs:` member. All three `github/codeql-action/{init,autobuild,analyze}` pins must share one SHA —
Dependabot group `codeql-action` (`github/codeql-action*` in `.github/dependabot.yml`) is what keeps
a bump atomic (one PR, three updates). `merge_group:` is an accepted juniper-ml-only divergence so
the context re-posts on a queued merge; do not overwrite the file with the `notes/templates/ci/`
snapshot. Full contract: [REFERENCE — CodeQL Analysis](REFERENCE.md#codeql-analysis).

**YubiKey ed448 `keytocard` (ml#904 / #914):** YubiKey 5 OpenPGP cannot hold Ed448/X448 — `KEYTOCARD failed:
Invalid value` is a hardware limit, not a bad PIN. Keep ed448 certify offline; put ed25519/cv25519
subkeys on the card. Procedure:
[notes/…YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md](../notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md).
Pointer: [REFERENCE — YubiKey GPG Provisioning](REFERENCE.md#yubikey-gpg-provisioning).

---

## Environment Variables

| Variable                       | Default            | Description                                             |
|--------------------------------|--------------------|---------------------------------------------------------|
| `WTC_SESSIONS_DIR`             | `scripts/sessions` | Session ID file storage directory                       |
| `WTC_LOGS_DIR`                 | `logs/`            | Headless mode log directory                             |
| `WTC_DEBUG`                    | `0`                | Enable launcher debug output                            |
| `CLAUDE_SKIP_PERMISSIONS`      | `0`                | Add `--dangerously-skip-permissions` to default wrapper |
| `JUNIPER_CASCOR_HOST`          | `localhost`        | Host stack cascor bind host for `util/juniper_plant_all.bash` |
| `JUNIPER_CASCOR_PORT`          | `8201`             | Host stack cascor listen port for `util/juniper_plant_all.bash` |
| `JUNIPER_DATA_HOST`            | `127.0.0.1`        | Host stack data-service bind host for `util/juniper_plant_all.bash` (loopback default; set `0.0.0.0` to expose) |
| `JUNIPER_DATA_PORT`            | `8100`             | Host stack data-service listen port for `util/juniper_plant_all.bash` |
| `JUNIPER_WORKER_HEALTH_HOST`   | `127.0.0.1`        | Host stack cascor-worker health listener bind host           |
| `JUNIPER_WORKER_HEALTH_PORT`   | `8210`             | Host stack cascor-worker health listener port           |
| `JUNIPER_PROJECT_DIR`          | `~/Development/python/Juniper` | Project root honored by `util/juniper_chop_all.bash`; `plant_all` derives the root from its script location |
| `KILL_WORKERS`                 | `0`                | Set to `1` so `chop_all` also runs `orphaned_worker_cleanup` (incl. on missing/empty pidfile abort); ignored under `--systemd` |
| `USE_SYSTEMD`                  | `0`                | `1` or `--systemd`: plant/chop via `systemctl --user` (no `JuniperProject.pid`) |
| `HEALTH_CHECK_TIMEOUT`         | `60`               | Seconds `util/juniper_plant_all.bash` waits for each service health gate |
| `HEALTH_CHECK_INTERVAL`        | `2`                | Seconds between health polls; non-positive/non-integer clamped to `1` (juniper-ml#782) |
| `JUNIPER_E2E_DATA_PORT`        | `8101`             | Isolated-stack juniper-data port (`util/isolated_stack.bash`) |
| `JUNIPER_E2E_CASCOR_PORT`      | `8202`             | Isolated-stack juniper-cascor port |
| `JUNIPER_E2E_CANOPY_PORT`      | `8051`             | Isolated-stack juniper-canopy port |
| `JUNIPER_E2E_HEALTH_TIMEOUT`   | `60`               | Per-service health wait for isolated `--up` (2s poll; not `HEALTH_CHECK_INTERVAL`) |
| `JUNIPER_E2E_RUN_DIR`          | `/tmp/juniper-e2e` | Scratch dir for data venv / logs / pidfiles |
| `JUNIPER_E2E_DATA_EXTRAS`      | `api`              | juniper-data pip extras (`api,mnist` for D2/I-5) |
| `CASCOR_HOST`                  | `localhost`        | CasCor query-helper target host for `util/get_cascor_*.bash` |
| `CASCOR_PORT`                  | `8201`             | CasCor query-helper target port for `util/get_cascor_*.bash` |
| `JUNIPER_FLEET_SKIP_PRECOMMIT` | unset              | When set, `predict_merge` skips the pre-commit battery (screens still run) |
| `JUNIPER_E2E_DATA_PORT`        | `8101`             | Isolated-stack juniper-data port (`util/isolated_stack.bash`) |
| `JUNIPER_E2E_CASCOR_PORT`      | `8202`             | Isolated-stack juniper-cascor port |
| `JUNIPER_E2E_CANOPY_PORT`      | `8051`             | Isolated-stack juniper-canopy port |
| `JUNIPER_E2E_HEALTH_TIMEOUT`   | `60`               | Per-service health wait for isolated `--up` |
| `JUNIPER_E2E_RUN_DIR`          | `/tmp/juniper-e2e` | Scratch dir for data venv / logs / pidfiles |
| `JUNIPER_E2E_DATA_EXTRAS`      | `api`              | juniper-data pip extras (`api,mnist` for D2/I-5) |
| `JUNIPER_E2E_CONDA_DIR`        | `/opt/miniforge3`  | Conda root for isolated cascor/canopy activate |
| `JUNIPER_EXP_RUN_ROOT`         | `~/.local/state/juniper-experiments` | Durable per-run root for `util/experiment_stack.bash` (not `/tmp`) |
| `JUNIPER_EXP_LOCK_ROOT`        | `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments` | Ephemeral port lockdirs (`8110`–`8289`) |
| `JUNIPER_EXP_PROJECT_DIR`      | parent of juniper-ml | Ecosystem root — **set in git worktrees** |
| `JUNIPER_EXP_HEALTH_TIMEOUT`   | `90`               | Per-service health wait for experiment `--up` (cold-start sized) |
| `JUNIPER_EXP_CONDA_DIR`        | `/opt/miniforge3`  | Conda root for experiment direct env-bin launch |
| `JUNIPER_REAP_PROC_ROOT`       | `/proc`            | Proc root for `util/reap_pytest_orphans.bash` (tests override) |
| `JUNIPER_REAP_KILL_CMD`        | `kill`             | Kill binary for `util/reap_pytest_orphans.bash` (tests override) |
| `JUNIPER_CASCOR_SNAPSHOTS_DIR` | `~/Development/python/Juniper/juniper-cascor/cascor-snapshots` | Dual-use: cascor write dir **and** snapshot-tool `--root` default. Do **not** redirect for the sidecar chain — pass `--root`. |
| `JUNIPER_CASCOR_SRC`           | `~/Development/python/Juniper/juniper-cascor/src` | Override cascor source tree for `snapshot_attribute.py` |
| `JUNIPER_DATA_ROOT`            | `~/Development/python/Juniper/juniper-data` | Override juniper-data tree for generator imports |
| `JUNIPER_FLEET_SKIP_PRECOMMIT` | unset              | When set, `predict_merge` skips the pre-commit battery (screens still run) |

Pitfall: `util/juniper_plant_all.bash` uses the `JUNIPER_CASCOR_*` names, while the `util/get_cascor_*.bash` query helpers use legacy `CASCOR_*` names.

Tip: before `/template-agent`, run `python util/agent_suite_doctor.py` (not `--no-discovery`). Discovery fail-closed: missing CLI, nonzero exit, non-JSON, or missing `schema_version`/`provenance.head_sha` → `FAIL`. See [REFERENCE.md § Agent Suite Doctor](REFERENCE.md#agent-suite-doctor).

Tip: before merging a Cursor-fleet batch, run `python util/fleet_triage/predict_merge.py --batch --json`. Prefer heal/`DAMAGED-FIX-FIRST` PRs first; never treat script exit `0` as “all clean” — read each `verdict`. Symbol screen matches `main-verify` (#895). See [REFERENCE.md § Fleet Triage](REFERENCE.md#fleet-triage-and-sequence-safety).

Tip: `util/isolated_stack.bash` is kill-by-port (not `JuniperProject.pid`). After `--down`, confirm `ss -tlnH 'sport = :8101 or sport = :8202 or sport = :8051'` is empty.
`data_up` needs `python3.14` on `PATH`, installs into `${JUNIPER_E2E_RUN_DIR}/.venv-data`, and launches with `PYTHON_GIL=0` (existing venv skips create but still re-pips). Use `JUNIPER_E2E_DATA_EXTRAS=api,mnist` for D2/I-5.
Post-[#785](https://github.com/pcalnon/juniper-ml/pull/785), `activate_conda` restores `set -u` after conda activate (pre-fix left nounset off for the rest of `--up`).
Full contract: [REFERENCE — Isolated Stack E2E](REFERENCE.md#isolated-stack-e2e-utilities).

Tip: `util/experiment_stack.bash` is the **per-run** launcher (data `8110–8139` / cascor `8230–8259` / recurrence `8260–8289`) — not isolated-stack and not `plant_all`. Never canopy; never `JuniperProject.pid`; never repo `.env`. Pidfiles come from post-health `ss` (F-6), not `$!`. From a worktree set `JUNIPER_EXP_PROJECT_DIR`. Drive with `python util/experiments/run_experiment.py --config … --run-dir …` (exit `0`–`4`). Full contract: [REFERENCE — Experiment Stack](REFERENCE.md#experiment-stack-utilities).

Tip: on a failed `*_up` leg, `do_up` auto-calls `teardown_run` (because `ports.json` is written before launches). Expect `bring-up failed — tearing the partial run back down`, then inspect `$RUN_DIR/logs/` + `teardown.json` before retrying. Pidfile refuse → kill-by-port on the recorded port only (open #923).

Tip: orphaned cascor workers outside `JuniperProject.pid` need `KILL_WORKERS=1 util/juniper_chop_all.bash` (default `0`). Strict filter keeps `juniper-cascor-worker` / `juniper_cascor_worker` only — not the old over-greedy `cascor.*worker`. Timeout hard-coded `5s`. Full contract: [REFERENCE — Host Orchestration](REFERENCE.md#host-orchestration-utilities).

Tip: never set `HEALTH_CHECK_INTERVAL=0` to "poll faster" — that busy-loops forever (`sleep 0` never advances elapsed).
Post-[#782](https://github.com/pcalnon/juniper-ml/pull/782), invalid/zero intervals log a WARNING and clamp to `1s`. Prefer the default `2`.

Tip: `python util/env_floor_drift_check.py --repo-root PATH [--env NAME|--site-packages DIR]` — precedence is `--site-packages` then `--env` then `ecosystem.yaml` `used_by`; exit `2` means resolution failed (not a floor finding). Multi-site keeps the **highest** installed version. Coverage: [#796](https://github.com/pcalnon/juniper-ml/pull/796) / [#802](https://github.com/pcalnon/juniper-ml/pull/802). Full contract: [REFERENCE — Environment Floor Drift](REFERENCE.md#environment-floor-drift-check).

Tip: after a crashed Juniper pytest session, run `util/reap_pytest_orphans.bash --dry-run` first. The awk gate keeps only current-user python whose cmdline has `JuniperC*` or `Juniper/worktrees/`; `skipped` is a ps→gone / missing-`PPid:` race, not a kill. See [REFERENCE.md § Pytest Orphan Reaper](REFERENCE.md#pytest-orphan-reaper).

Tip: `python util/editable_install_drift_check.py --fix --json` is the live mutation path (`action=FIXED` on success). `ERROR` (pip/`OSError`) truncates detail to 500 chars and continues the plan — re-scan still exits `1` while orphans remain. Preview with `--dry-run` first. Coverage: [#802](https://github.com/pcalnon/juniper-ml/pull/802). Full contract: [REFERENCE — Editable Install Drift](REFERENCE.md#editable-install-drift-check).

Tip: `FRESH` does **not** mean up to date. An editable's `*.dist-info/METADATA` is frozen at the last `pip install -e`, so `import` follows the live tree while `importlib.metadata.version()` reports the old number — that is what fails a repo's own `version == pyproject` self-check and makes a host-launched service export a wrong build-info version. The `STALE` column catches it (soft by default; `--strict-version` to fail, `--fix --fix-stale` to re-stamp). Scope with `--env NAME` when a long-lived service is running from an env.

Tip: missing **or** empty (zero-byte) `JuniperProject.pid` → `chop_all` still calls `orphaned_worker_cleanup`, then `exit 1`, and never enters the service-stop loop. Early cleanup sites are hard (no `|| true`); post-pidfile cleanup is soft. Default `KILL_WORKERS=0` only logs the short-circuit — use `KILL_WORKERS=1` when orphaned workers may be the only leftovers. See [`REFERENCE.md`](REFERENCE.md#missing--empty-juniperprojectpid-early-wire).

Tip: non-empty `JuniperProject.pid` → `chop_all` validates each PID against `/proc/<pid>/cmdline` before SIGTERM (JR-ML-SEC-045). Accepts `name=pid` and legacy `name: pid`. Reused-PID mismatch → WARNING skip (not a stop failure); successful chop still truncates the pidfile. `STOP_FAILURES > 0` preserves it. See [`REFERENCE.md`](REFERENCE.md#non-empty-pidfile-stop-path-validate_pid).

Tip: systemd plant does **not** track units in `STARTED_PIDS` — a mid-plant health failure leaves started user units running; tear down with `util/juniper_chop_all.bash --systemd` (see `docs/REFERENCE.md` § systemd mode).

Tip: systemd chop soft-fails per unit and always exits `0` without touching the pidfile / `KILL_WORKERS` path — do not expect orphaned-worker cleanup in that mode.

Tip: `util/install_duplicati_timer.bash` **copies** the Duplicati runner/units (a worktree symlink dies with `git worktree remove`) and does **not** `enable --now`.
Linger must be `yes`; `~/.config/duplicati-backup/env` must be mode `600` with `PASSPHRASE=`. `--no-auto-compact=true` is load-bearing.
A skip overwrites `result=OK`, so the next skip always escalates. Distinct from `util/juniper-backup.bash`.
Full contract: [REFERENCE — Scheduled Duplicati Backup Lane](REFERENCE.md#scheduled-duplicati-backup-lane).

Tip: before merging a Cursor-fleet batch, run `python util/fleet_triage/predict_merge.py --batch --json`.
Prefer heal PRs first (title/branch tokens `restore`/`heal`/`repair`/`fix-first` sort ahead of colliding
feat PRs); never treat script exit `0` as “all clean” — read each `verdict`. Symbol screen matches
`main-verify` (#895). Docs screen is stricter (any removed `.md` line; unified-diff `---` headers never
count) but honors `Allow-Docs-Rewrite` trailers (#926). Docs-only PRs skip the pre-commit battery.
See [REFERENCE.md § Fleet Triage](REFERENCE.md#fleet-triage-and-sequence-safety).

Tip: flood CI gates (#869/#880) — per-PR `Sequence Safety` / `Fleet PR Lint` are **advisory** (not in Quality Gate `needs:`). Labels `allow-symbol-loss` / `docs-rewrite` only demote the PR job via `--advisory`; post-merge `main-verify` needs commit trailers. G4 uses `--from-ref` on PR/merge_group and `--all-files` on push. Full contract: [REFERENCE.md § Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates).

Tip: `gpg: KEYTOCARD failed: Invalid value` for ed448 on a YubiKey 5 is expected — card has no Curve448. Do not burn Admin PIN retries; follow the ed25519/cv25519 subkey layout in [REFERENCE — YubiKey GPG](REFERENCE.md#yubikey-gpg-provisioning). Stub pinentry must greet with Assuan `OK` (#914). An Ed448 *creation* refusal needing `--compliance=gnupg` is the Ubuntu/Debian FreePG-patched build, not upstream GnuPG.

Tip: CI Quality Gate (`ci.yml` → `required-checks`) must **not** list `sequence-safety` / `fleet-pr-lint` / `release-train-archive-guard` in `needs:` — they skip on push while the gate is `if: always()`. `security` alone soft-fails (`== "failure"`, so a skip stays green); every other need is `!= "success"`. Post-merge `main-verify`'s battery path-gates on `tests/`\|`util/`\|`scripts/`\|`.github/`\|`pyproject.toml` and **fails open** to `run=true` when no base resolves (initial / force push). Full contract: [REFERENCE — Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) / [Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification).

Tip: scheduled `security-scan.yml` keeps `pip-audit --strict --desc on` (no `--skip-editable`); the per-PR `ci.yml` security job is the deliberate opposite (`--skip-editable`, no `--strict`) so an editable meta install cannot redden every PR. Weekly `lockfile-update.yml` must call `juniper-generate-dep-docs` (never resurrect `util/generate_dep_docs.sh`, deleted in #298) and open `chore/lockfile-update` with labels `dependencies` + `automated`. See [REFERENCE — Scheduled Security Scan and Lockfile Update](REFERENCE.md#scheduled-security-scan-and-lockfile-update).

Tip: two clone/audit lists move together. `docs-full-check.yml` `env.ECOSYSTEM_REPOS` decides which siblings are *cloned*; `DEFAULT_REPOS` in `util/validate_claude_yaml_access.bash` decides which cloned checkouts the `claude.yml` auditor *opens*. Both are "registry publishing repos plus `juniper-deploy`" — adding a sibling to one only leaves a silent gap. See [REFERENCE — Docs Full Check](REFERENCE.md#docs-full-check) and [Claude.yml Access Validation](REFERENCE.md#claudeyml-access-validation).

**Claude Code Action (`claude.yml`):** GitHub `@claude` assistant, not the local `claudey` /
`wake_the_claude.bash` launcher. SHA-pinned `anthropics/claude-code-action` (`# vX.Y.Z` comment);
only input is `secrets.ANTHROPIC_API_KEY` (a **repo** secret). The job `if:` requires the literal
`@claude` on every `on:` event. Dependabot groups only `codeql-action` — an ungrouped
`claude-code-action` SHA bump is the healthy PR. Do not overwrite the live file with
`notes/templates/ci/claude.yml` (2026-04-29 snapshot). Full contract:
[REFERENCE — Claude Code Action](REFERENCE.md#claude-code-action).

Tip: meta publish Gate 1 polls TestPyPI 10×6s (~60s ceiling) for the just-uploaded wheel, then runs **three** local-wheel installs (bare → `[clients]` → `[tools]`; never `--no-deps` on the installs, never `--extra-index-url`, never the heavy extras) before PyPI. Do not restore `sleep 30`.

Tip: the six shared `publish-*.yml` are Release-only (`release: published`; no `push: tags` — the #555 double-publish race); a bare `git push <tag>` starts **no run**. Each is tag-prefix-guarded, with a `--no-deps` TestPyPI-only 5×10s verify and `skip-existing: true`. Do not resurrect a `Require a GitHub Release for this tag` step under `if: github.event_name == 'push'` — that condition is unreachable (#1310). See [REFERENCE — Build and Release](REFERENCE.md#build-and-release).

Tip: shared-package `ci-*.yml` (six sub-packages) must keep path self-inclusion, matrix floors, `--cov-fail-under`, and a blocking `juniper-coverage-gap-map --enforce`. Dropping the workflow self-path or `--enforce` ships green while the package suite stops running or stops enforcing gaps; service-core installs sibling `juniper-model-core` from the monorepo root (no test-job `working-directory`). Full table: [REFERENCE — Shared-Package CI](REFERENCE.md#shared-package-ci-workflows).

Tip: editing `AGENTS.md` on any PR triggers `agents-md-touch-up.yml`, which **verifies** `**Last Updated**:` — it must be a valid `YYYY-MM-DD`, not in the future, and changed in your PR. Bump it yourself in the same commit (`**Last Updated**: $(date -u +%Y-%m-%d)`); the job never edits your branch. A missing field warns and passes. Since juniper-ml#1099 there is **no** bot commit: the old auto-bump produced unsigned commits (rejected by `required_signatures`) and `[skip ci]` heads that orphaned every required check. See [REFERENCE — AGENTS.md Date Check](REFERENCE.md#agentsmd-date-check).

Tip: release-train detect footers — report/propose count `UNRELEASED_CHANGES` + `BUMPED_NOT_RELEASED` + `SHIP_UNCERTAIN`; the **ceremony** footer counts only `BUMPED_NOT_RELEASED`. A missing/empty `release-manifest.json` shows the hard-fail banner (`FAILED HARD` in Slack), never a quiet clear. See [REFERENCE — Detect Summary and Slack](REFERENCE.md#release-train-detect-summary-and-slack).

Tip: on a failed `*_up` leg, isolated-stack `do_up` auto-calls `do_down` — expect `bring-up failed — tearing the partial trio back down`, then check `$JUNIPER_E2E_RUN_DIR/logs/` and confirm the ports are free before retrying. `activate_conda` is fail-closed (`if ! conda activate …; then set -u; return 1; fi`), so a bad env name aborts the leg instead of launching on the ambient PATH.

Tip: `experiment_stack.bash` legs are OR-listed (`*_up || failed=1`), which disables `set -e` inside each body — critical steps need `|| return 1` or a health timeout with a live listener false-greens `--up` and skips teardown. A `--grafana-bridge` failure after healthy services tears the run down; a **staging** failure (missing `--config`) still exits between `allocate_port` and `ports.json`, so clear stale `*.lock` dirs under `JUNIPER_EXP_LOCK_ROOT` by hand (open #979).

Tip: a renderer `ValueError` is a per-plot SKIP (exit `0`, no PNG); missing matplotlib, a failed payload fetch, or any other render exception is SKIP **and** acceptance failure (exit `1`). Inspect `jq '.driver.plots' $RUN_DIR/manifest.json`. See [REFERENCE — Plot SKIP vs acceptance](REFERENCE.md#plot-skip-vs-acceptance-valueerror-contract).

Tip: juniper-service-core invariants — `RequestBodyLimitMiddleware` always stream-caps POST/PUT/PATCH (`Content-Length` is a hint only); auth runs before rate limiting and 429s must pass `exc.headers` through; control-WS reject logs stay single-line via `_sanitize_for_log`; `ws_control_rate_limit_per_sec=0` yields `retry_after=3600` instead of dividing by zero; `/ws/workers` closes **4001** on bad auth and **4008** on a bad registration shape. See [REFERENCE — juniper-service-core](REFERENCE.md#juniper-service-core).

Tip: REST client `base_url` on GitHub-main data/cascor/recurrence clients is normalised (case-insensitive scheme, `hostname` required, trailing `/v1` stripped). `HTTPS://host` on an older wheel silently becomes `http://HTTPS://host`. Cascor WS streams stay rstrip-only. Host cascor is `:8201`, constructor default is `:8200`. See [REFERENCE — HTTP Client Base-URL](REFERENCE.md#http-client-base-url-contract).

Tip: `predict_merge --pr` **hard-fails** (exit `2`) when `gh` exits nonzero or returns non-JSON, while `--batch` soft-`ERROR`s that row and keeps going. A deleted `.py` stays in `true_delta` for the symbol screen but is filtered out of the pre-commit battery, so a pure-deletion PR can be gate-clean and still `DAMAGED-FIX-FIRST`.

Tip: snapshot attribution is not reproducible until juniper-ml#1333. `--seed` only samples which snapshots to score; `--dataset-seed` (default `DATASET_SEED=20260824`) pins generators that declare `seed=None`. spiral keeps its own seed. Do not export `JUNIPER_CASCOR_SNAPSHOTS_DIR` for the sidecar chain — pass `--root`. See [REFERENCE — Snapshot Attribution Dataset Pin](REFERENCE.md#snapshot-attribution-dataset-pin).


### Host Stack Troubleshooting

| Symptom | Fast Check |
|---------|------------|
| `@claude` mention did nothing | Job `if:` needs the literal `@claude` in that event's body (or issue title); `issues: assigned` still needs it |
| Copied `notes/templates/ci/claude.yml` onto live | Template snapshot lags Dependabot (checkout v6.0.2 / action v1.0.107); restore `.github/workflows/claude.yml` from `main` |
| L2/L3 auditor green after permissions widen | Expected — bash is structure-only; `LiveClaudeWorkflowContractTests` pins the map |
| Slack PR-budget WARN/ALARM | Open the `PR Budget Alarm` run step summary; drain oldest `cursor/` same-file clusters; confirm dashboard per-run caps. Raise thresholds only via `PR_BUDGET_WARN` / `PR_BUDGET_ALARM` repo vars. |
| Budget alarm cron green but no Slack on breach | Confirm `SLACK_WEBHOOK_URL` is set; missing secret skips notification by design (run stays green). |
| `predict_merge` exit `2` | Bad args / non-git `--repo-root` / missing `gh` / unresolved branch ref — not a damage finding. |
| `DAMAGED-FIX-FIRST` on intentional delete | Add `Allow-Symbol-Loss: func:…` (qualified) on a commit in the PR; re-run `--pr`. Label alone will not green `main-verify`. |
| Local triage stuck in pre-commit | `JUNIPER_FLEET_SKIP_PRECOMMIT=1` (screens still run). |
| Startup exits before launching services | Check the preflight output for missing `curl`, `ss`, conda, sibling repo directories, or occupied ports. |
| Mid-plant abort / health timeout | Service log under that repo's `logs/`; pidfile is already removed — free leftover listeners with `ss -tlnp` before re-planting. |
| Cascor health times out | Inspect `juniper-cascor/logs/juniper-cascor_*.log`; keep the default `JuniperCascor1` env unless a replacement is known-good. |
| Freeze tell exit 0, then editing primary corrupts a service | Exit 0 ≠ no importer — root-owned holds are invisible. Confirm with privileged `lsof` on `PRIMARY/src` before editing. |
| Freeze tell flags `juniper-cascor-client` / a worktree | Live tell uses an exact prefix; siblings and both worktree roots are not holds. A remaining hit is importing the **primary**. |
| Worker binary missing | Run `conda activate JuniperCascor1 && pip install juniper-cascor-worker`. |
| `chop_all` cannot find `JuniperProject.pid` | Confirm `plant_all` finished in `nohup` mode and rerun with `JUNIPER_PROJECT_DIR` set to the same project root; for systemd mode, stop with `util/juniper_chop_all.bash --systemd`. |
| Doctor green but Template Agent grounding dead | Re-run without `--no-discovery`; fix `util/prompt_discovery/cli.py` until it emits `schema_version` + `provenance.head_sha`. |
| `predict_merge` exit `2` | Bad args / non-git `--repo-root` / missing `gh` — not a damage finding. (Unresolved tip in `--batch` is soft-`ERROR`, exit 0.) |
| New `.md` falsely `DAMAGED-FIX-FIRST` | Header-counting bug class: only content `-` lines count; `---` file headers must be ignored (#910). |
| Docs-only PR “fails” gates | No `.py` in TRUE delta → battery `skip` (`no .py files in delta`), not fail. |
| Heal PR not first in `--batch` order | Title or branch needs `restore`/`heal`/`repair`/`fix-first` (not bare `fix`/`hotfix`). |
| Local triage stuck in pre-commit | `JUNIPER_FLEET_SKIP_PRECOMMIT=1` (screens still run). |
| `ast_symbol_screen.status=skip` in JSON | Checker missing/exit 2/non-JSON — **not** damage (#908). |
| Isolated `--up` missing `python3.14` | Put `python3.14` on `PATH`; abort is before venv/pid create. |
| Isolated data health / GIL oddities | Confirm `PYTHON_GIL=0` in launch; check `$JUNIPER_E2E_RUN_DIR/logs/juniper-data.log`. |
| Isolated `--up` unset-var / odd conda failure | Need #785 nounset restore; check `JUNIPER_E2E_CONDA_DIR`. |
| Isolated ports still busy after `--down` | Re-run `--down` or kill the `pid=` from `ss -tlnpH`; `--dry-run` never kills. |
| Isolated health timeout | Inspect `/tmp/juniper-e2e/logs/*.log` (or `$JUNIPER_E2E_RUN_DIR/logs`); raise `JUNIPER_E2E_HEALTH_TIMEOUT` only after fixing the service. |
| Experiment `--up` misuse / exit `2` | Need one action + `--cascor` and/or `--recurrence`. |
| Experiment health timeout | Check `$RUN_DIR/logs/`; default wait is `90s` (cold recurrence). Set `JUNIPER_EXP_PROJECT_DIR` in worktrees. |
| Experiment `bring-up failed` / partial stack | `do_up` already ran `teardown_run` — read `teardown.json` + logs; confirm lockdirs gone before retry. |
| Experiment `pidfile path refused` | Pid-reuse refuse → kill-by-port on the recorded port only; WARNING means inspect `ss` before reuse (open #923). |
| Experiment teardown left listeners / wrong kill | Confirm F-6 pidfiles (`record_listener_pid` after health); `--down` keeps `artifacts/`. |
| Driver exit `1` stalled/timed_out | Cascor stall detector / wall budget; recurrence `timed_out` = train socket budget. See `manifest.json`. |
| `chop_all` logs `ERROR: PID file is empty` | Zero-byte pidfile is the empty arm of the same early wire (cleanup then `exit 1`). Re-plant; do not hand-create an empty file. |
| Missing/empty pidfile but workers still up | Early wire already invoked cleanup; set `KILL_WORKERS=1` on that chop to opt into the pgrep reap before abort. |
| Chop WARNING `cmdline does not match … skipping` | Stale/reused PID — `validate_pid` refused the kill; not a stop failure. Pidfile still truncates when `STOP_FAILURES == 0`. |
| Chop preserves pidfile after WARNING stop failures | A `graceful_stop` failed — inspect survivors (`ss -tlnp`), then re-chop or kill manually. |
| systemd plant: missing `curl` | Install/expose `curl`; abort is before any `systemctl start`. |
| systemd plant partial after health timeout | Run `util/juniper_chop_all.bash --systemd` (ERR cleanup does not `systemctl stop`). |
| Duplicati installer refuses `env` / mode / Linger | `~/.config/duplicati-backup/env` mode `600` with `PASSPHRASE=`; `loginctl enable-linger $USER` |
| Duplicati timer silent after logout | Linger was `no` — the original failure class. Confirm `list-timers duplicati-backup.timer` |
| Duplicati `FATAL` unmounted dest / tmpfs tempdir | Mount the backup volume; point `DUPLICATI_TEMP_DIR` at any disk-backed path (the runner refuses a RAM-backed one outright, and `/tmp` is tmpfs here) |
| Duplicati skip then next run escalates | Expected — skip overwrites `result=OK`. Inspect `~/.local/state/duplicati/{last-run.status,failures.log}` |
| `predict_merge` exit `2` | Bad args / non-git `--repo-root` / missing `gh` / unresolved branch ref — not a damage finding. |
| Fleet `DAMAGED` on intentional docs rewrite | Add `Allow-Docs-Rewrite: <path>` or `*` in BASE..RESULT (#926); wrong-path trailers do not waive. |
| Mixed `--systemd` / pidfile modes | Match plant and chop modes; systemd never writes `JuniperProject.pid`. |
| Plant WARNING `invalid health-check interval` / stuck health wait | Unset `HEALTH_CHECK_INTERVAL` or set a positive integer (default `2`); `0` was a busy-loop. |
| `env_floor_drift_check` exits `2` | Resolution failed (`resolve_site_dirs`) — fix `--site-packages` / `--env` / `ecosystem.yaml` `used_by`; not a `BELOW_FLOOR`. |
| Unexpected `BELOW_FLOOR` after upgrade | Multi-interpreter env may still hold a lower tree — tool reports the highest across site-packages; upgrade or remove the stale tree. |
| `--fix` JSON shows `ERROR` mid-plan | Inspect `error` (stderr/`OSError`, ≤500 chars); fix env python / pip cause; re-run `--fix`. Other items may already be `FIXED`. |
| Sequence Safety red, Quality Gate green | Advisory by design — download `sequence-safety-report`; waive with trailers or (owner) labels |
| Label greens Sequence Safety; `main-verify` fails | Put `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` on a landed commit; labels are PR-only |
| Merge queue stalled (no required check) | Confirm `ci.yml` **and** `codeql.yml` `on.merge_group` still present; `Analyze (python)` must re-post |
| `Analyze (python)` red: version mismatch | `init`/`autobuild`/`analyze` SHAs split — align to one SHA; keep Dependabot group `codeql-action` |
| Checks green, merge `BLOCKED` (CodeQL) | Unresolved CodeQL review thread (not in the check rollup) — fix the finding in code |
| Waiting for results from CodeQL | Ruleset `code_scanning` has no SARIF yet — wait for `Analyze (python)`; restore `merge_group` if a queued merge never gets a context |
| Tiny PR still fails global doc-link hook | G4: `pass_filenames: false` hooks still run repo-wide under `--from-ref` |
| `KEYTOCARD failed: Invalid value` (ed448) | Hardware — YubiKey 5 OpenPGP has no Ed448; use ed25519/cv25519 subkeys. See [REFERENCE](REFERENCE.md#yubikey-gpg-provisioning). |
| Stub pinentry “No pinentry” / dead agent | Assuan greeting must be `OK …` (#914); check `util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash`. Throwaway creds only. |
| Ed448 keygen fails under gpg 2.4 | Ubuntu/Debian FreePG-patched build (not upstream) — add `--compliance=gnupg` (or `compliance gnupg` in ceremony `gpg.conf`). |
| Every `push:main` Quality Gate red; advisory job "skipped" | An advisory job was added to `required-checks.needs` — remove it; promote via branch ruleset instead. |
| Security job skipped → Quality Gate red | The security arm must stay `== "failure"`, not `!= "success"`. |
| Initial / force-push tip skipped the battery | The path detector must fail-open to `run=true` when no base resolves — read the `Detect relevant path changes` log. |
| Weekly security scan green with a known CVE | Audit step must stay `pip-audit --strict --desc on`; dropping `--strict` softens findings. |
| Scheduled security scan suddenly fails every run | Someone added `--skip-editable` — that flag belongs only to per-PR `ci.yml`. |
| No Monday lockfile PR | A clean tree is a no-op; confirm Actions → Update Lockfiles still runs `juniper-generate-dep-docs`. |
| `test_ci_tools_drift` red after a ci-tools bump | Widen the `<Y` ceiling in `lockfile-update.yml` + `ci.yml` + `docs-full-check.yml` in the same PR. |
| `Verify AGENTS.md Last Updated` fails | You changed `AGENTS.md` without bumping `**Last Updated**:`. Set it to today's UTC date and push. |
| `AGENTS.md` date not auto-bumped | Fork PR (skipped by design), missing `**Last Updated**:` field (warning only), or the date is already today. |
| A shared-package workflow edit never runs its CI | `paths:` must still list the workflow file itself. |
| Coverage gap map "passes" on a hollow module | Look for a dropped `--enforce` or a newly broad `--omit`. |
| Isolated `bring-up failed` / partial trio | `do_up` already ran `do_down` — read the logs, confirm the ports are free, then retry. |
| Isolated `--up` logs `ERROR: conda activate '…' failed` | Expected fail-closed path — fix the env name or `JUNIPER_E2E_CONDA_DIR`, then retry. |
| Experiment `--up` green but ports/locks stuck | OR-list false-green — confirm the `\|\| return 1` pins; `--down <RUN_ID>`, then clear stale `*.lock`. |
| Experiment `grafana bridge failed — tearing the run back down` | Expected `--grafana-bridge` teardown; install `socat`/`docker` or omit the flag. |
| Experiment port range exhausted after a failed `--config` | Staging aborted between `allocate_port` and `ports.json` (open #979) — clear `*.lock` under `JUNIPER_EXP_LOCK_ROOT` with no live listener. |
| Plot `skipped` with a `ValueError` reason, exit `0` | No-renderable-data SKIP, not an acceptance failure — see `jq '.driver.plots' $RUN_DIR/manifest.json`. |
| Driver exit `1` `matplotlib unavailable` | Install matplotlib or drop `outputs.plots`; other render exceptions and fetch failures also fail acceptance. |
| `residuals.png` has only 2 panels | Optional `target_dt_*` missing or length-mismatched — pred/truth still plotted; not a SKIP. |
| HTTP 429 missing `Retry-After` | `SecurityMiddleware` must pass `exc.headers` into the `JSONResponse`. |
| `Juniper*ConfigurationError: base_url must include a host` | Hostless constructor URL (`""`, `http://`, `http://user:secret@`) — fix the URL, not the service. |
| `HTTPS://host` talks HTTP / hostname `https` | Wheel predates case-insensitive scheme matching; install client GitHub main or wait for the next PyPI cut. |
| Cascor REST connection refused on `:8200` | Constructor default is the container port; host stack publishes `:8201`. |
| WS stream does not default `ws://` / reject hostless | Deliberate — `CascorTrainingStream` / `CascorControlStream` only `rstrip("/")`. |
| A probe gets 429 on `/v1/health` | Health/docs/metrics are exempt in service-core — check an upstream proxy or a non-exempt path. |
| Large POST accepted despite the body limit | The mutating-method stream cap must be unconditional; a `Content-Length`-only fast path is the bypass. |
| Control-WS reject log spans multiple lines | `_sanitize_for_log` regression — never interpolate raw Origin/command into logger format strings. |
| Worker WS closes 4001 / 4008 | 4001 = API-key auth enabled (send `X-API-Key`); 4008 = registration shape (string `worker_id` + dict `capabilities`). |
| `--batch` row `verdict=ERROR` | Soft-fail for that tip only; the other PRs in the report remain valid. `--pr` would have exited `2` instead. |
| Deleted `.py` gate-clean but `DAMAGED` | The battery skipped the missing path while the symbol screen saw `LOST` — expected. |
| Two identical attribution runs differ | Unpinned generators (need #1333). `--seed` samples snapshots; `--dataset-seed` pins data. |
| Sidecar chain wrote into scratch / empty archive | `JUNIPER_CASCOR_SNAPSHOTS_DIR` was redirected — unset it and pass `--root`. |
| `--write` exits 2 before scoring | `--sample` / `--min-hidden` / `--from-sidecar` with `--write` is refused so the sidecar cannot cover a subset. |

## Quick Reference Tables

| Service               | Host Port | Health                    | Conda Env       | Python |
|-----------------------|-----------|---------------------------|-----------------|--------|
| juniper-data          | 8100      | `GET /v1/health`          | JuniperData     | 3.14   |
| juniper-cascor        | 8201      | `GET /v1/health`          | JuniperCascor1  | 3.13   |
| juniper-canopy        | 8050      | `GET /v1/health`          | JuniperCanopy1  | 3.13   |
| juniper-cascor-worker | 8210      | `GET /v1/health/ready`    | JuniperCascor1  | 3.13   |

Isolated E2E trio (never overlap these with the host ports above):

| Service        | E2E Port | Health           | Runtime                         |
|----------------|----------|------------------|---------------------------------|
| juniper-data   | 8101     | `GET /v1/health` | dedicated `python3.14` venv     |
| juniper-cascor | 8202     | `GET /v1/health` | `JuniperCascor1`                |
| juniper-canopy | 8051     | `GET /v1/health` | `JuniperCanopy1` (service mode) |

`juniper-cascor` still commonly exposes service/container port `8200`; host-mode utilities and Docker's published port use `8201`.

Isolated E2E trio (never overlap these with the host ports above):

| Service        | E2E Port | Health           | Runtime                         |
|----------------|----------|------------------|---------------------------------|
| juniper-data   | 8101     | `GET /v1/health` | dedicated `python3.14` venv     |
| juniper-cascor | 8202     | `GET /v1/health` | `JuniperCascor1` + empty `LD_LIBRARY_PATH` |
| juniper-canopy | 8051     | `GET /v1/health` | `JuniperCanopy1`, `DEMO_MODE=0` |

Metric pattern: `<namespace>_<subsystem>_<metric>_<unit>` -- namespaces: `juniper_data_*`, `juniper_cascor_*`, `juniper_canopy_*`

---

## Cross-References

- [Ecosystem Guide](../AGENTS.md) -- project map, dependency graph, conventions
- [juniper-ml REFERENCE](REFERENCE.md) -- package metadata, extras, version history
- [Claude Code Action](REFERENCE.md#claude-code-action) -- live `claude.yml` pin, `@claude` `if:`, ungrouped Dependabot bumps
- [CodeQL Analysis](REFERENCE.md#codeql-analysis) -- `Analyze (python)`, SHA group, `merge_group` divergence
- [Deprecated Master Cheatsheet](../notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md) -- archived monolithic cross-project reference (relocated to `notes/history/` in 2026-04, consolidated into `notes/legacy/` 2026-05-05)
- [Cascor Primary Freeze Tell](REFERENCE.md#cascor-primary-freeze-tell) -- exact-prefix hold test; exit 0 is "no user-owned importer"
- [Worktree Setup](../notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) | [Worktree Cleanup V2](../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md)
- [SOPS Usage Guide](../notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md) -- complete secrets management reference

---

**Last Updated:** 2026-09-04
**Version:** 1.0.56
**Maintainer:** Paul Calnon
