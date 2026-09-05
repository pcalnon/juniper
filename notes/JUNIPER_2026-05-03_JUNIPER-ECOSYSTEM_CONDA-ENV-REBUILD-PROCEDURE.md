# Juniper conda env rebuild procedure (P-5)

**Author:** Paul Calnon
**Date:** 2026-05-03
**Scope:** `JuniperCascor`, `JuniperCanopy`, `JuniperData` conda envs

Operator surface (exit codes; **2** is this free-threaded class, **4** is the May-7 wheel-layout class): [`docs/REFERENCE.md` § Conda Env Torch Shadow Diagnostic](../docs/REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5). Classify with `util/check_conda_env_torch.bash` before rebuilding.

---

## 1. Symptom

`import torch` from any Juniper conda env raises:

```text
ImportError: Failed to load PyTorch C extensions:
    It appears that PyTorch has loaded the `torch/_C` folder
    of the PyTorch repository rather than the C extensions which
    are expected in the `torch._C` namespace.
```

Affects every cascor/canopy local repro that needs torch. Tracked as
**P-5** in [`JUNIPER_2026-05-03_JUNIPER-CASCOR_POST-V38-OPEN-ISSUES-PLAN.md`](./JUNIPER_2026-05-03_JUNIPER-CASCOR_POST-V38-OPEN-ISSUES-PLAN.md).
The error has blocked local diagnosis of P-1 (RC-4 multiprocessing
race) since the V38 cycle.

## 2. Diagnosis

The conda envs have drifted to **free-threaded Python 3.14t**
(`cp314t` ABI tag) but the installed torch wheel is built for
**regular Python 3.14** (`cp314` ABI tag). Concretely, in a broken
env:

```bash
$ /opt/miniforge3/envs/JuniperCascor/bin/python -c "import sys; print(sys.version)"
3.14.3 free-threading build | packaged by conda-forge
                ^^^^^^^^^^^^^^

$ ls /opt/miniforge3/envs/JuniperCascor/lib/python3.14/site-packages/torch/_C*
torch/_C.cpython-314-x86_64-linux-gnu.so   # regular cp314 ABI, NOT cp314t
torch/_C/__init__.pyi                       # type stubs (always shipped)
torch/_C/_VariableFunctions.pyi
```

The interpreter (`cp314t`) skips the `.so` because the ABI tag
doesn't match, falls back to the `_C/` directory as a namespace
package (since it has no `__init__.py`), and torch's
`from torch._C import _initExtension` then fails because the
namespace package only contains `.pyi` stubs.

The conda lockfile pin in
`juniper-cascor/conf/conda_environment.yaml:77` is
`python=3.14.2=h32b2ec7_100_cp314` (regular ABI, no `t` suffix), so
the YAML is correct — the live env drifted via a manual
`mamba install python-freethreading` or similar.

The `JuniperCascor1` and `JuniperCanopy1` envs (suffixed `1`) are
the recovery envs the team has been using since the drift was
discovered. `JuniperCascor1` is on regular Python 3.13 with torch
2.11.0 and imports cleanly:

```bash
$ /opt/miniforge3/envs/JuniperCascor1/bin/python -c "import torch; print(torch.__version__)"
2.11.0+cu130
```

## 3. Recovery procedure

### Option A — use the existing recovery env (zero rebuild)

Cheapest path. `JuniperCascor1` already works. For local development:

```bash
conda activate JuniperCascor1   # instead of JuniperCascor
```

If you want `JuniperCascor` to point to the working env:

```bash
mamba rename JuniperCascor JuniperCascor-broken-cp314t-backup
mamba rename JuniperCascor1 JuniperCascor
```

This preserves the broken env as a backup until you're confident the
rebuild path works.

### Option B — full rebuild on regular Python 3.13

Use this when you want a clean lockfile aligned with what CI runs
(CI matrix tests Python 3.12/3.13/3.14 on regular CPython, not FT —
see `juniper-cascor/.github/workflows/ci.yml`).

```bash
# Back up the broken env's name, but leave it on disk for now in
# case rebuild fails partway.
mamba rename JuniperCascor JuniperCascor-broken-cp314t-backup

# Create a fresh env on Python 3.13 (regular CPython, no FT).
mamba create -n JuniperCascor python=3.13 -c conda-forge

conda activate JuniperCascor

# Install runtime deps. CPU-only torch index avoids pulling 4 GB of
# CUDA wheels on machines without a GPU.
pip install torch --index-url https://download.pytorch.org/whl/cpu
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
pip install -e ".[all]"

# Verify
python -c "import torch; print('torch', torch.__version__, 'OK')"
python -m pytest -m "unit and not slow" src/tests/unit -q --maxfail=5
```

When the new env works, capture the lockfile so future rebuilds are
reproducible:

```bash
conda list --explicit > conf/conda_environment.yaml
```

### Option C — repair the broken env in place

For the brave. Force the env's Python ABI tag back to regular `cp314`:

```bash
mamba install -n JuniperCascor python=3.14 python_abi=3.14=*_cp314 \
  --override-channels -c conda-forge
```

This typically fails because conda refuses to downgrade
`python-freethreading`-pulled deps cleanly. Skip this option unless
you've already invested in it.

## 4. Verification

The repaired env must satisfy all four checks:

```bash
# 1. Python is regular CPython (no "free-threading build" in version).
python -c "import sys; print(sys.version)"

# 2. python_abi is cp313 or cp314 (no `t` suffix).
conda list python_abi

# 3. torch imports cleanly.
python -c "import torch; print('torch', torch.__version__)"

# 4. The torch._C namespace resolves to a .so, not a directory.
python -c "import torch._C as c; print(c.__file__)"
# Expected: ...site-packages/torch/_C.cpython-313-x86_64-linux-gnu.so
# (or cpython-314, never cpython-314t)
```

If any of these fail, the env is still broken — back out and use
Option A.

## 5. Cross-project note

`JuniperCanopy` has the same shadow on Python 3.14t. The same
procedure applies — substitute `JuniperCanopy` for `JuniperCascor`
throughout, and `juniper-canopy` for `juniper-cascor` in the
`pip install -e ".[all]"` step.

`JuniperCanopy1` (the recovery env) has a separate, unrelated bug:

```text
ImportError: /home/pcalnon/Development/rust/rust_mudgeon/juniper/libs/libtorch/lib/libtorch_python.so:
             undefined symbol: _PyObject_NextNotImplemented
```

— a leaked `LD_LIBRARY_PATH` or rust-mudgeon-build artefact pulling
in the wrong `libtorch_python.so`. Out of scope for P-5; track
separately if the canopy rebuild needs it.

`JuniperData` has no torch installed (its workload is dataset
generation, not training), so the shadow doesn't affect it. The
P-5 plan-doc entry was over-broad.

## 6. Why this happened

The conda lockfile YAML pins `cp314` (regular). The drift to `cp314t`
came from out-of-band `mamba install` operations exploring
free-threading torch — likely during the V38 RC-4 investigation,
when free-threaded Python was being evaluated as an alternative to
multiprocessing for candidate training. The investigation was
inconclusive (FT torch wheels for cp314t are not yet broadly
published), but the env never got rolled back.

## 7. Going forward

- Don't manually `mamba install python-freethreading` into the
  Juniper envs without also updating the project's
  `conf/conda_environment.yaml` lockfile.
- Free-threading exploration belongs in a separate sandbox env
  (e.g. `JuniperCascor-FT`) so the working `JuniperCascor` env stays
  stable.
- Once `JuniperCanopy1`'s `libtorch_python.so` issue is sorted, treat
  the `*1` envs as canonical and retire the original `JuniperCascor`
  / `JuniperCanopy` names via `mamba rename`.
