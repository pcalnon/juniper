# Developer Cheatsheet — juniper-ml

**Version**: 1.0.6
**Date**: 2026-07-26
**Project**: juniper-ml

---

## Common Commands

| Command                                                | Description                                     |
|--------------------------------------------------------|-------------------------------------------------|
| `pip install -e ".[all]"`                              | Install meta-package with all extras (editable; multi-GB — pulls torch via `[worker]`) |
| `pip install -e ".[clients]"`                          | Install just the HTTP/WS client libraries (editable) |
| `pip install -e ".[worker]"`                           | Install just the distributed training worker (editable) |
| `pip install -e ".[servers]"`                          | Install just the service distributions: canopy + cascor + data (editable) |
| `pip install -e ".[tools]"`                            | Install just shared tooling: ci-tools + doc-tools + observability (editable) |
| `python -m build && twine check dist/*`                | Build and validate package                      |
| `python3 -m unittest -v tests/test_wake_the_claude.py` | Run launcher regression tests                   |
| `python3 -m unittest -v tests/test_pyproject_extras.py`| Lint pyproject.toml extras structure            |
| `bash scripts/test_resume_file_safety.bash`            | Run resume file safety regression               |
| `pre-commit run --all-files`                           | Run all pre-commit hooks                        |
| `juniper-check-doc-links --cross-repo skip`            | Validate doc links (CI-parity mode; install via `pip install juniper-doc-tools`) |
| `util/juniper_plant_all.bash`                          | Start the host-level Juniper stack with health gates |
| `util/get_cascor_status.bash`                          | Query host-mode cascor status (`CASCOR_HOST` / `CASCOR_PORT`, default `localhost:8201`) |
| `util/juniper_chop_all.bash`                           | Stop the host-level stack from `JuniperProject.pid` |
| `util/isolated_stack.bash --up` / `--down` / `--status` | Throwaway E2E trio on 8101/8202/8051 (use `--dry-run` to preview) |
| `./claudey`                                            | Launch default interactive Claude session       |

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
3. **Add optional group**: Add under `[project.optional-dependencies]`, include in `all`, update `AGENTS.md` and `README.md`

> See: per-repo `pyproject.toml` | `juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md`

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
| Publish | Push tag `juniper-observability-vX.Y.Z` to trigger `.github/workflows/publish-observability.yml` |
| Retry publish | Use `workflow_dispatch` on `.github/workflows/publish-observability.yml` against the existing tag |

Publish flow: build uploads `juniper-observability-dist` for seven days, TestPyPI downloads and publishes it with OIDC, TestPyPI install is retried for index lag, then PyPI downloads the same artifact after TestPyPI verification succeeds.

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

---

## CI/CD

| Task                   | Command / Procedure                                                                         |
|------------------------|---------------------------------------------------------------------------------------------|
| Pre-commit             | `pre-commit run --all-files`                                                                |
| Publish `juniper-ml`   | Create GitHub Release with `vX.Y.Z` tag (OIDC trusted publishing)                           |
| Publish observability  | Push `juniper-observability-vX.Y.Z` tag (OIDC trusted publishing)                           |
| Publish doc-tools      | Push `juniper-doc-tools-vX.Y.Z` tag (OIDC trusted publishing)                               |
| Doc links (CI parity)  | `juniper-check-doc-links --exclude templates --exclude history --exclude legacy --cross-repo skip` |
| Doc links (full local) | `juniper-check-doc-links --cross-repo check`                                                |

Key hooks: `ruff` (juniper-data) or `black`+`isort`+`flake8` (others), `mypy`, `bandit`, `shellcheck`, `no-unencrypted-env`.

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

**Release-train `packages` dispatch + `--cross-repo`.** Both write jobs reject garbage
`packages` tokens (`Juniper-Observability`, underscores, `../`, `;`) with exit **2** + `::error::`
before python runs; empty = all eligible; commas ≡ whitespace. `--cross-repo` only when `APP_TOKEN`
is non-empty. Runbook §3.2; pin juniper-ml#729 `PackagesInputRehearsalTest`.

**Release-train write-job git identity (ml#705):** when editing `.github/workflows/release-train.yml`, keep both `propose` and `ceremony` identity steps on `git config --global user.name|user.email|commit.gpgsign` (never bare repo-local `git config`). Cross-repo commits land in freshly-cloned sibling checkouts; a juniper-ml-only identity leaves them with `Author identity unknown` (run 30040138774). Operator detail: runbook §7 / §8.7.

**Release-train propose step summary:** after `mode=propose`, read the job step summary — it buckets
`propose.py`'s `opened:` / `skip:` lines into Opened / Skipped sections. An empty `propose-output.txt`
shows `produced no output` (crash); a non-empty no-op shows `0` / `0` without that banner. Detail:
runbook §3.2. Hermetic pin: juniper-ml#730 (`ProposeSummaryRehearsalTest`).

**Release-train ceremony archive reuse:** re-dispatching `ceremony` while an exempt notes-archive PR is
still open reuses it (no duplicate open; `--auto` arms on the archive **branch**). If the notes file is
already on `main`, ceremony cuts the Release only (no archive-PR / auto-merge calls). Do not close a
healthy open archive PR to "start over". Detail: runbook §3.3 / §5.5. Hermetic pin: juniper-ml#730.

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
| `HEALTH_CHECK_TIMEOUT`         | `60`               | Seconds `util/juniper_plant_all.bash` waits for each service health gate |
| `JUNIPER_E2E_DATA_PORT`        | `8101`             | Isolated-stack juniper-data port (`util/isolated_stack.bash`) |
| `JUNIPER_E2E_CASCOR_PORT`      | `8202`             | Isolated-stack juniper-cascor port |
| `JUNIPER_E2E_CANOPY_PORT`      | `8051`             | Isolated-stack juniper-canopy port |
| `JUNIPER_E2E_HEALTH_TIMEOUT`   | `60`               | Per-service health wait for isolated `--up` (2s poll; not `HEALTH_CHECK_INTERVAL`) |
| `JUNIPER_E2E_RUN_DIR`          | `/tmp/juniper-e2e` | Scratch dir for data venv / logs / pidfiles |
| `JUNIPER_E2E_DATA_EXTRAS`      | `api`              | juniper-data pip extras (`api,mnist` for D2/I-5) |
| `CASCOR_HOST`                  | `localhost`        | CasCor query-helper target host for `util/get_cascor_*.bash` |
| `CASCOR_PORT`                  | `8201`             | CasCor query-helper target port for `util/get_cascor_*.bash` |

Pitfall: `util/juniper_plant_all.bash` uses the `JUNIPER_CASCOR_*` names, while the `util/get_cascor_*.bash` query helpers use legacy `CASCOR_*` names.

Tip: `util/isolated_stack.bash` is kill-by-port (not `JuniperProject.pid`). After `--down`, confirm `ss -tlnH 'sport = :8101 or sport = :8202 or sport = :8051'` is empty.
Post-[#785](https://github.com/pcalnon/juniper-ml/pull/785), `activate_conda` restores `set -u` after conda activate (pre-fix left nounset off for the rest of `--up`).
Full contract: [REFERENCE — Isolated Stack E2E](REFERENCE.md#isolated-stack-e2e-utilities).

Tip: `plant_all` `safe_conda_activate` must restore nounset with `set -u` after `conda activate` (ADDR2LINE class). A `set +u`/`set +u` pair silently disables `set -u` for the rest of host bring-up — same bug class as isolated-stack [#785](https://github.com/pcalnon/juniper-ml/pull/785). Coverage: [#795](https://github.com/pcalnon/juniper-ml/pull/795).

Tip: `python util/editable_install_drift_check.py --fix --dry-run --json` SKIPs when two non-worktree trees share a `[project].name` (`reason` contains `ambiguous`; never `candidates[0]`). Resolve the duplicate checkout, then re-run. Coverage: [#795](https://github.com/pcalnon/juniper-ml/pull/795). Full contract: [REFERENCE — Editable Install Drift](REFERENCE.md#editable-install-drift-check).

### Host Stack Troubleshooting

| Symptom | Fast Check |
|---------|------------|
| Startup exits before launching services | Check the preflight output for missing `curl`, `ss`, conda, sibling repo directories, or occupied ports. |
| Mid-plant abort / health timeout | Service log under that repo's `logs/`; pidfile is already removed — free leftover listeners with `ss -tlnp` before re-planting. |
| Cascor health times out | Inspect `juniper-cascor/logs/juniper-cascor_*.log`; keep the default `JuniperCascor1` env unless a replacement is known-good. |
| Worker binary missing | Run `conda activate JuniperCascor1 && pip install juniper-cascor-worker`. |
| `chop_all` cannot find `JuniperProject.pid` | Confirm `plant_all` finished in `nohup` mode and rerun with `JUNIPER_PROJECT_DIR` set to the same project root; for systemd mode, stop with `util/juniper_chop_all.bash --systemd`. |
| Isolated `--up` unset-var / odd conda failure | Need #785 nounset restore; check `JUNIPER_E2E_CONDA_DIR`. |
| Isolated ports still busy after `--down` | Re-run `--down` or kill the `pid=` from `ss -tlnpH`; `--dry-run` never kills. |
| Isolated health timeout | Inspect `/tmp/juniper-e2e/logs/*.log` (or `$JUNIPER_E2E_RUN_DIR/logs`); raise `JUNIPER_E2E_HEALTH_TIMEOUT` only after fixing the service. |
| Mid-plant unset-var / odd conda failure | Confirm `safe_conda_activate` ends with `set -u` (`rg -n -A3 '^safe_conda_activate' util/juniper_plant_all.bash`). |
| `--fix` JSON shows `ambiguous` SKIP | Two checkouts share the package name — remove/rename the extra tree; do not hand-pick `candidates[0]`. |

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

Metric pattern: `<namespace>_<subsystem>_<metric>_<unit>` -- namespaces: `juniper_data_*`, `juniper_cascor_*`, `juniper_canopy_*`

---

## Cross-References

- [Ecosystem Guide](../AGENTS.md) -- project map, dependency graph, conventions
- [juniper-ml REFERENCE](REFERENCE.md) -- package metadata, extras, version history
- [Deprecated Master Cheatsheet](../notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md) -- archived monolithic cross-project reference (relocated to `notes/history/` in 2026-04, consolidated into `notes/legacy/` 2026-05-05)
- [Worktree Setup](../notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) | [Worktree Cleanup V2](../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md)
- [SOPS Usage Guide](../notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md) -- complete secrets management reference

---

**Last Updated:** 2026-07-26
**Version:** 1.0.6
**Maintainer:** Paul Calnon
