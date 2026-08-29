# Publishing a Python Package to PyPI

A step-by-step procedure for publishing a Python package to the Python Package Index (PyPI), using the `juniper-ml` meta-package as a concrete example throughout.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure and Metadata](#2-project-structure-and-metadata)
3. [PyPI and TestPyPI Account Setup](#3-pypi-and-testpypi-account-setup)
4. [Building the Package Locally](#4-building-the-package-locally)
5. [Validating the Package](#5-validating-the-package)
6. [Publishing to TestPyPI (Manual)](#6-publishing-to-testpypi-manual)
7. [Verifying the TestPyPI Upload](#7-verifying-the-testpypi-upload)
8. [Publishing to PyPI (Manual)](#8-publishing-to-pypi-manual)
9. [Verifying the PyPI Upload](#9-verifying-the-pypi-upload)
10. [Automating with GitHub Actions (Trusted Publishing)](#10-automating-with-github-actions-trusted-publishing)
11. [Cutting a Release (End-to-End)](#11-cutting-a-release-end-to-end)
12. [Troubleshooting](#12-troubleshooting)
13. [Reference Links](#13-reference-links)

---

## 1. Prerequisites

### Tools

Install the build and upload toolchain:

```bash
pip install build twine
```

| Tool | Purpose |
|------|---------|
| `build` | PEP 517 frontend — builds sdist and wheel from `pyproject.toml` |
| `twine` | Uploads distributions to PyPI/TestPyPI and validates package metadata |

### Accounts

- **PyPI**: https://pypi.org/account/register/
- **TestPyPI**: https://test.pypi.org/account/register/

These are separate registries with separate accounts. Register on both.

### API Tokens (for manual uploads)

On each registry, go to **Account Settings > API tokens** and create a token:

- **Scope**: Project-scoped tokens are preferred over account-wide tokens. For a first upload (before the project exists on PyPI), you must use an account-wide token, then replace it with a project-scoped token afterward.
- **Storage**: Save tokens in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

Set restrictive permissions:

```bash
chmod 600 ~/.pypirc
```

> **Note**: If using GitHub Actions with trusted publishing (OIDC), API tokens are not needed for CI uploads. See [Section 10](#10-automating-with-github-actions-trusted-publishing).

---

## 2. Project Structure and Metadata

### Minimum required files

```
juniper/
├── pyproject.toml    # Package metadata, build system, dependencies
├── README.md         # Long description (rendered on PyPI project page)
└── LICENSE           # License file
```

### pyproject.toml — the single source of truth

The `juniper-ml` package uses `setuptools` as the build backend. Here is its `pyproject.toml` annotated with key fields:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]    # Build dependencies
build-backend = "setuptools.build_meta"      # PEP 517 backend

[project]
name = "juniper-ml"                          # PyPI package name (must be globally unique)
version = "0.1.0"                            # SemVer — bump this before each release
description = "Juniper - Cascade Correlation Neural Network Research Platform"
readme = "README.md"                         # Rendered as the PyPI long description
license = "MIT"
authors = [{ name = "Paul Calnon" }]
requires-python = ">=3.12"
keywords = ["juniper", "cascade-correlation", "neural-network", "machine-learning"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3.12",
    # ... additional classifiers
]
dependencies = []                            # Runtime deps (empty for a meta-package)

[project.optional-dependencies]              # pip install juniper-ml[clients]
clients = [
    "juniper-data-client>=0.3.0",
    "juniper-cascor-client>=0.1.0",
]
worker = [
    "juniper-cascor-worker>=0.1.0",
]
all = [
    "juniper[clients,worker]",               # Composite extra
]

[project.urls]
Homepage = "https://github.com/pcalnon/juniper-ml"
Repository = "https://github.com/pcalnon/juniper-ml"
Issues = "https://github.com/pcalnon/juniper-ml/issues"
```

### Key metadata decisions

| Field | Guidance |
|-------|----------|
| `name` | Must be unique on PyPI. Normalized: underscores, hyphens, and periods are equivalent (`juniper-ml` == `juniper_ml`). Check availability at `https://pypi.org/project/<name>/`. |
| `version` | Follow [SemVer](https://semver.org/). Must be incremented for every upload — PyPI will reject a version that already exists, even if the prior upload was deleted. |
| `readme` | Supports Markdown (`.md`) or reStructuredText (`.rst`). PyPI renders this as the project landing page. |
| `classifiers` | Selected from the [official list](https://pypi.org/classifiers/). Helps users discover your package. |
| `requires-python` | Enforced at install time. Users on unsupported Python versions will get an error or receive an older compatible version. |

---

## 3. PyPI and TestPyPI Account Setup

### 3.1 Enable two-factor authentication (2FA)

PyPI requires 2FA for all accounts. Enable it under **Account Settings > Two factor authentication** using a TOTP app or hardware security key.

### 3.2 Create the project (first upload)

The project is automatically created on PyPI/TestPyPI the first time you upload a distribution with that package name. There is no separate "create project" step.

### 3.3 Configure trusted publishing (for GitHub Actions)

If you plan to automate publishing via GitHub Actions (recommended), configure trusted publishing **before your first automated upload**:

1. Go to **PyPI > Your Projects > (project name) > Settings > Publishing** (or for a new project: **Account Settings > Publishing > Add a new pending publisher**)
2. Fill in:
   - **Owner**: Your GitHub username or organization (e.g., `pcalnon`)
   - **Repository**: The repo name (e.g., `juniper`)
   - **Workflow name**: The filename of the workflow (e.g., `publish.yml`)
   - **Environment name**: The GitHub Actions environment (e.g., `pypi` or `testpypi`)
3. Repeat for TestPyPI if you use it as a staging step.

This eliminates the need for API tokens in CI. The workflow authenticates via OIDC.

---

## 4. Building the Package Locally

From the project root (where `pyproject.toml` lives):

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build both sdist (.tar.gz) and wheel (.whl)
python -m build
```

This produces files in `dist/`:

```
dist/
├── juniper_ml-0.1.0.tar.gz       # Source distribution
└── juniper_ml-0.1.0-py3-none-any.whl  # Built distribution (wheel)
```

### What gets built

| Artifact | Format | Description |
|----------|--------|-------------|
| sdist | `.tar.gz` | Source archive — includes `pyproject.toml`, `README.md`, `LICENSE`, and any source code |
| wheel | `.whl` | Pre-built distribution — faster to install, no build step required at install time |

### Build tags explained

The wheel filename `juniper_ml-0.1.0-py3-none-any.whl` encodes compatibility:

- `py3` — Python 3 only
- `none` — No ABI dependency (pure Python)
- `any` — Platform-independent

---

## 5. Validating the Package

### 5.1 Check metadata and rendering

```bash
twine check dist/*
```

This validates:
- Package metadata is well-formed
- `README.md` renders correctly (catches Markdown/RST issues that would break the PyPI page)

Expected output:

```
Checking dist/juniper_ml-0.1.0.tar.gz: PASSED
Checking dist/juniper_ml-0.1.0-py3-none-any.whl: PASSED
```

### 5.2 Inspect the wheel contents

```bash
unzip -l dist/juniper_ml-0.1.0-py3-none-any.whl
```

Verify it contains the expected files (metadata, license, readme) and nothing unexpected (stray test files, `.env` files, etc.).

### 5.3 Test a local install

```bash
# Create an isolated venv
python -m venv /tmp/test-install
source /tmp/test-install/bin/activate

# Install from the built wheel
pip install dist/juniper_ml-0.1.0-py3-none-any.whl

# Verify
pip show juniper-ml

# Clean up
deactivate
rm -rf /tmp/test-install
```

---

## 6. Publishing to TestPyPI (Manual)

TestPyPI is a staging environment that mirrors PyPI. Always upload here first.

```bash
twine upload --repository testpypi dist/*
```

If not using `~/.pypirc`, you can pass credentials inline:

```bash
twine upload --repository-url https://test.pypi.org/legacy/ \
    --username __token__ \
    --password pypi-YOUR_TESTPYPI_TOKEN \
    dist/*
```

Expected output:

```
Uploading juniper_ml-0.1.0.tar.gz
Uploading juniper_ml-0.1.0-py3-none-any.whl
View at: https://test.pypi.org/project/juniper-ml/0.1.0/
```

---

## 7. Verifying the TestPyPI Upload

### 7.1 Check the project page

Visit `https://test.pypi.org/project/juniper-ml/0.1.0/` and verify:
- Description renders correctly
- Metadata (author, license, classifiers) is correct
- Project links work

### 7.2 Test installation from TestPyPI

```bash
python -m venv /tmp/test-testpypi
source /tmp/test-testpypi/bin/activate

# --extra-index-url ensures real dependencies resolve from PyPI
pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    juniper-ml==0.1.0

pip show juniper-ml

deactivate
rm -rf /tmp/test-testpypi
```

> **Important**: The `--extra-index-url https://pypi.org/simple/` flag is essential. TestPyPI does not host all packages — without this fallback, dependencies will fail to resolve.

> **2026-08-08 amendment — the CI meta-verify no longer uses the merged-index form above (owner-approved two-phase mechanism)**: pip has **no index priority**, so `--index-url` + `--extra-index-url` collapse into ONE namespace where the *highest version across both indexes wins* — a dependency-confusion vector in which a TestPyPI squatter outranks the real package (live failure: TestPyPI `fastapi 1.0`, a broken sdist, beat production `fastapi 0.141.1` and killed the juniper-ml v0.7.0 verify, run 31281873275). `.github/workflows/publish.yml` now verifies in two phases — **(1) provenance**: `pip download --no-deps --index-url https://test.pypi.org/simple/ --dest <tmp> "juniper-ml==${VERSION}"` (TestPyPI only, exact version), then **(2) resolution**: `pip install --index-url https://pypi.org/simple/ "<wheel>[extra]"` (production PyPI only, no `--no-deps`, so extras resolution is still genuinely exercised). The one-index-at-a-time rule is the point; the manual recipe above remains merged-namespace and is therefore subject to the same squatting risk. Gate: `tests/test_publish_testpypi_verify.py`.

---

## 8. Publishing to PyPI (Manual)

Once TestPyPI is verified:

```bash
twine upload dist/*
```

Or explicitly:

```bash
twine upload --repository pypi dist/*
```

> **This is irreversible for the version number.** Once `0.1.0` is uploaded and then deleted, you can never upload `0.1.0` again. You would need to bump to `0.1.1`.

---

## 9. Verifying the PyPI Upload

### 9.1 Check the project page

Visit `https://pypi.org/project/juniper-ml/0.1.0/`.

### 9.2 Test installation from PyPI

```bash
python -m venv /tmp/test-pypi
source /tmp/test-pypi/bin/activate

pip install juniper-ml==0.1.0
pip show juniper-ml

# Test optional extras
pip install "juniper-ml[all]==0.1.0"

deactivate
rm -rf /tmp/test-pypi
```

---

## 10. Automating with GitHub Actions (Trusted Publishing)

Manual uploads work but are error-prone and non-auditable. The recommended approach is CI/CD automation using GitHub Actions with trusted publishing (OIDC).

### 10.1 How trusted publishing works

Instead of storing API tokens as GitHub secrets, PyPI verifies the identity of the GitHub Actions workflow itself via OpenID Connect (OIDC). The workflow requests a short-lived token from PyPI, scoped to the specific project and environment.

Requirements:
- The GitHub repository must be registered as a trusted publisher on PyPI (see [Section 3.3](#33-configure-trusted-publishing-for-github-actions))
- The workflow must have `id-token: write` permission
- The workflow must use a named GitHub environment matching the one registered on PyPI

### 10.2 Workflow file

The `juniper-ml` project uses `.github/workflows/publish.yml`. The YAML below is the **original simplified design**, not the live workflow — see the 2026-08-08 and 2026-08-24 amendments after §10.3. Live contract: [`docs/REFERENCE.md` § Meta-Package Publish Pipeline](../docs/REFERENCE.md#meta-package-publish-pipeline).

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]              # Triggered by creating a GitHub Release

permissions:
  id-token: write                   # Required for OIDC trusted publishing

jobs:
  testpypi:
    name: Publish to TestPyPI
    runs-on: ubuntu-latest
    environment: testpypi           # Must match the TestPyPI trusted publisher config
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

      - name: Verify TestPyPI install
        run: |
          VERSION="${{ github.event.release.tag_name }}"
          VERSION="${VERSION#v}"      # Strip leading 'v' (v0.1.0 -> 0.1.0)
          sleep 30                    # Wait for TestPyPI index to update
          pip install \
              --index-url https://test.pypi.org/simple/ \
              --extra-index-url https://pypi.org/simple/ \
              juniper-ml==${VERSION}

  pypi:
    name: Publish to PyPI
    needs: testpypi                  # Only runs if TestPyPI succeeds
    runs-on: ubuntu-latest
    environment: pypi                # Must match the PyPI trusted publisher config
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### 10.3 Key design decisions in this workflow

| Decision | Rationale |
|----------|-----------|
| TestPyPI runs first, PyPI depends on it (`needs: testpypi`) | Catches packaging errors before the irreversible PyPI upload |
| Verification step installs from TestPyPI after upload | Confirms the package is actually installable, not just uploadable |
| `sleep 30` before verification install | **Historical.** TestPyPI index propagation can lag. Live `publish.yml` (juniper-ml#1310) replaced this with a bounded 10×6s `pip download` poll (~60s ceiling); do not restore the fixed sleep. |
| Separate GitHub environments (`testpypi`, `pypi`) | Each maps to its own trusted publisher configuration; enables environment-level protection rules (e.g., manual approval for `pypi`) |
| Rebuild in the `pypi` job instead of passing artifacts | **Historical.** Live workflows upload a `dist/` artifact from `build` and download it in the publish jobs. |
| `id-token: write` at the top level | **Historical.** P4 (juniper-ml#357) scopes `id-token: write` to the two publish jobs only; the build job restates `contents: read`. |

> **2026-08-24 amendment (juniper-ml#1310).** Two live-workflow corrections against the snippet above.
>
> 1. **Bounded poll, not `sleep 30`.** TestPyPI's simple index is CDN-fronted and lags ~5–30s, so the first fetch of a just-published version can 404. A fixed sleep is wrong in both directions: paid in full when the index is already warm (77% of a measured 39s step), and still a coin-flip when propagation runs long. Live Gate 1 polls `pip download --no-deps` from TestPyPI-only, 10 attempts × 6s (~60s ceiling), then a real `::error::` if the version is never served. The fetch stays on one parseable line (`tests/test_publish_testpypi_verify.py` matches `^pip download`). Sibling publishers retry `pip install --no-deps` five times with a 10s interval.
> 2. **The trigger is the gate.** The six sub-package publishers used to carry a `Require a GitHub Release for this tag` step gated on `if: github.event_name == 'push'`. None of them subscribe to `push:` (removed after #555, where Release-plus-push raced the immutable TestPyPI upload), so those steps could never run. Dead code shaped like a guard is worse than no guard. With `release: published` as the only automatic trigger, a bare `git push <tag>` starts **no run**. Gate: `tests/test_publish_release_only_trigger.py` (glob-discovered; pins both directions). Re-measured 2026-08-24: 12 tags exist with no Release and none of them published.

### 10.4 GitHub environment setup

Create two environments in **GitHub > Repository > Settings > Environments**:

1. **`testpypi`**
   - No special protection rules needed
   - Used for staging uploads

2. **`pypi`**
   - Recommended: Add a **required reviewer** protection rule so production publishes require manual approval
   - Optional: Restrict to the `main` branch

---

## 11. Cutting a Release (End-to-End)

This is the complete procedure from "code is ready" to "package is live on PyPI."

> **Release convention (mandatory).** Every PyPI deploy — the meta-package **and** every shared /
> sub-package — is performed by **cutting a GitHub Release**, never by pushing a bare tag, and the
> release notes are **archived under `notes/releases/`**. The Release (and its archived notes) is the
> durable, auditable record of the deploy; the tag the Release creates is what triggers the publish
> workflow. This convention drifted during rapid concurrent development (several sub-packages shipped
> tag-only, with no Release and no archived notes) and is being restored — see §11.3–§11.4.

### 11.1 Bump the version

Edit `pyproject.toml`:

```toml
version = "0.2.0"    # was "0.1.0"
```

### 11.2 Commit and push

```bash
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push origin main
```

### 11.3 Author and archive the release notes

Write the notes from [`notes/templates/TEMPLATE_RELEASE_NOTES.md`](templates/TEMPLATE_RELEASE_NOTES.md)
and **archive a copy in the central `juniper-ml/notes/releases/` archive** (committed in the release
PR) so every ecosystem release has one in-repo record alongside its GitHub Release body. The archive
is **central**: releases cut from *other* repos (e.g. juniper-recurrence, juniper-cascor) are archived
here too, not in their own repos.

- Meta-package (`juniper-ml`): `RELEASE_NOTES_v<version>.md`
- Every other package — a shared sub-package *or* a package from another repo: `RELEASE_NOTES_<pkg>_v<version>.md`
  (e.g. `RELEASE_NOTES_juniper-model-core_v0.2.0.md`, `RELEASE_NOTES_juniper-cascor_v0.5.0.md`). The
  package prefix is required so same-version tags across packages (e.g. juniper-ml `v0.5.0` vs
  juniper-cascor `v0.5.0`) never collide.

### 11.4 Cut the GitHub Release (this is the deploy — never a bare tag)

Cutting the Release is what creates the tag and triggers the publish workflow. **Do not
`git push <tag>` by hand** — always go through a Release so the deploy has a durable, auditable
record. For the meta-package the Release event triggers `publish.yml`; for a shared / sub-package the
Release **creates the `juniper-<pkg>-v*` tag**, which triggers that package's `publish-<pkg>.yml`.

#### Option A: GitHub CLI

```bash
# Meta-package (tag v<version>):
gh release create v0.2.0 --title "v0.2.0" \
    --notes-file notes/releases/RELEASE_NOTES_v0.2.0.md --latest

# Shared / sub-package (tag juniper-<pkg>-v<version>); --latest=false keeps the meta-package's badge:
gh release create juniper-model-core-v0.2.0 \
    --title "juniper-model-core v0.2.0 — <headline>" \
    --notes-file notes/releases/RELEASE_NOTES_juniper-model-core_v0.2.0.md --latest=false
```

#### Option B: GitHub Web UI

1. Go to **Releases > Draft a new release**
2. **Create** the tag inline — `v<version>` (meta) or `juniper-<pkg>-v<version>` (sub-package)
3. Set the title and paste the archived release notes
4. Click **Publish release**

### 11.5 Monitor the workflow

```bash
gh run list --workflow=publish.yml --limit=1
gh run watch                       # Live tail the run
```

Or visit **Actions** tab in the repository.

### 11.6 Verify

```bash
pip install juniper-ml==0.2.0
pip show juniper-ml
```

---

## 12. Troubleshooting

### Upload rejected: "File already exists"

PyPI does not allow re-uploading the same version, even if the previous upload was deleted. Bump the version number (e.g., `0.1.0` -> `0.1.1`).

### twine check fails: "warning: The description failed to render"

Your `README.md` has syntax that PyPI's renderer cannot handle. Common causes:
- Raw HTML that is not allowed
- Relative image links (use absolute URLs)
- Unsupported Markdown extensions

Test rendering locally:

```bash
pip install readme-renderer[md]
python -m readme_renderer README.md -o /tmp/readme.html
```

### TestPyPI install fails with "No matching distribution found"

- The index may not have propagated yet. Live Gate 1 polls for ~60s (10×6s); sibling publishers retry 5×10s. A remaining 404 after that ceiling is a real miss, not lag — check that the version string matches exactly (no leading `v`)
- Do not restore an unconditional `sleep 30` in `.github/workflows/publish.yml`; that sleep was neither necessary nor sufficient (juniper-ml#1310)
- Manual install from TestPyPI still needs `--extra-index-url https://pypi.org/simple/` so *dependencies* resolve, but that merged-namespace form is the squatting risk the CI two-phase verify exists to avoid (see §7.2 2026-08-08 amendment)

### Trusted publishing fails: "Token request failed"

- Verify the repository, workflow filename, and environment name match exactly between GitHub and PyPI's trusted publisher settings
- Ensure the workflow has `permissions: id-token: write`
- Check that the GitHub environment name in the `environment:` field matches the one registered on PyPI (case-sensitive)

### "This package name is not available"

The name is taken on PyPI (check `https://pypi.org/project/<name>/`). Choose a different `name` in `pyproject.toml`. Normalization means `my-package`, `my_package`, and `my.package` are all equivalent.

### Build produces unexpected files in the wheel

Add or update the `[tool.setuptools]` section to control what's included:

```toml
[tool.setuptools]
packages = []    # Meta-package: no Python packages to include
```

Or use a `MANIFEST.in` to control what goes into the sdist.

---

## 13. Reference Links

| Resource | URL |
|----------|-----|
| PyPI | https://pypi.org/ |
| TestPyPI | https://test.pypi.org/ |
| Python Packaging User Guide | https://packaging.python.org/ |
| `pyproject.toml` specification | https://packaging.python.org/en/latest/specifications/pyproject-toml/ |
| Trusted Publishing docs | https://docs.pypi.org/trusted-publishers/ |
| `pypa/gh-action-pypi-publish` | https://github.com/pypa/gh-action-pypi-publish |
| PyPI classifiers list | https://pypi.org/classifiers/ |
| SemVer specification | https://semver.org/ |
