# Juniper CI workflow templates

These files are the **canonical sources** referenced by the cross-repo CI
pipeline alignment plan (`notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-PIPELINE-ALIGNMENT-PLAN.md`).

## Files

| Template | Purpose | Per-repo customization |
|---|---|---|
| `claude.yml` | `@claude` PR/issue assistant | Copy the **live** juniper-ml workflow; this file is a 2026-04-29 snapshot |
| `codeql.yml` | CodeQL semantic SAST (Python) | None for Python repos |
| `scheduled-tests.yml` | Daily slow / integration suite | `PYTHON_TEST_VERSION` env + `pytest -m` selector |
| `lockfile-update.yml` | Weekly `requirements_ci.txt` refresh PR | None — relies on `util/generate_dep_docs.sh` if present |
| `security-scan-deploy.yml` | Infra-flavored security scan (trivy + SOPS) for juniper-deploy | Lands as `security-scan.yml` in juniper-deploy with `continue-on-error: true` for the shakedown cycle |

## Required secrets

- `claude.yml` requires repo secret `ANTHROPIC_API_KEY`. Owner `pcalnon` is a
  personal account, so there are no org-scoped Actions secrets (walkthrough §1.1).

## How to roll out

For each target repo, copy the applicable templates into the repo's
`.github/workflows/` and customize the values flagged in each file's
header. The §6 per-repo plan in
`notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-PIPELINE-ALIGNMENT-PLAN.md` lists the exact set
of templates each repo needs. Exception: for `claude.yml`, copy juniper-ml's
**live** `.github/workflows/claude.yml` rather than this snapshot.

## Action / version pins

The pinned action SHAs match the rest of the fleet's existing
workflows as of 2026-04-29:

- `actions/checkout@v6.0.2` → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `actions/setup-python@v6.2.0` → `a309ff8b426b58ec0e2a45f0f869d46889d02405`
- `actions/upload-artifact@v7.0.1` → `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
- `github/codeql-action@v4.35.2` → `95e58e9a2cdfd71adc6e0353d5c52f41a045d225`
- `anthropics/claude-code-action@v1.0.107` → `567fe954a4527e81f132d87d1bdbcc94f7737434`
- `aquasecurity/trivy-action@0.34.0` → `dc5a429b52fcf669ce959baa2c2dd26090d2a6c4`
- `peter-evans/create-pull-request@v7.0.5` → `271a8d0340265f705aeb70568e08251a5f6ed72b`

Dependabot will keep these current after rollout. **Do not treat this table as live pins.**
The 2026-04-29 snapshot lags the fleet: juniper-ml's live `claude.yml` SHA-pins
`actions/checkout` and `anthropics/claude-code-action` independently of this table
(the action moves by ungrouped Dependabot PR). Operator surface:
[`docs/REFERENCE.md` § Claude Code Action](../../docs/REFERENCE.md#claude-code-action).

The 2026-04-29 snapshot lags the fleet: juniper-ml's CodeQL pins, the `codeql-action` Dependabot
group, and the accepted `merge_group` trigger live in `.github/workflows/codeql.yml`. Operator
surface: [`docs/REFERENCE.md` § CodeQL Analysis](../../docs/REFERENCE.md#codeql-analysis).
