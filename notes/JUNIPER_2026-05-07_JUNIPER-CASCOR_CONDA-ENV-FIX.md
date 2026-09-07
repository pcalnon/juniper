# CasCor Conda Env Fix — 2026-05-07

**Status**: shipped
**Author**: Paul Calnon (executed by Claude Code)
**Scope**: `util/juniper_plant_all.bash`, `/opt/miniforge3/envs/JuniperCascor{,1}/etc/conda/{activate,deactivate}.d/`

Operator surface (this regular-3.14 wheel-layout class is exit **4**, not P-5's exit **2**): [`docs/REFERENCE.md` § Conda Env Torch Shadow Diagnostic](../docs/REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5). Classify with `util/check_conda_env_torch.bash` before flipping `JUNIPER_CASCOR_CONDA`.

---

## 1. Symptom

Running `./util/juniper_plant_all.bash` failed during the cascor stage:

```
[juniper_plant_all.bash:408] === Starting juniper-cascor ===
… (60s pass) …
[juniper_plant_all.bash:wait_for_health] juniper-cascor: timeout reached, /v1/health never returned 2xx
```

The cascor server log (`juniper-cascor/logs/juniper-cascor_*.log`) showed the
process dying immediately at import time:

```
File "/home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/app.py", line 11, in <module>
    import torch
File "/opt/miniforge3/envs/JuniperCascor/lib/python3.14/site-packages/torch/__init__.py", line 1013, in <module>
ImportError: Failed to load PyTorch C extensions:
    It appears that PyTorch has loaded the `torch/_C` folder
    of the PyTorch repository rather than the C extensions which
    are expected in the `torch._C` namespace.
```

The server never bound to port 8201, so `wait_for_health` looped until
`HEALTH_CHECK_TIMEOUT` expired.

---

## 2. Root cause — torch wheel layout bug under Python 3.14

The `JuniperCascor` env (Python 3.14.3 + torch 2.9.1) ships **both**:

- `torch/_C.cpython-314-x86_64-linux-gnu.so` — the actual compiled C extension
- `torch/_C/` — a directory containing `.pyi` type stubs

Under PEP 420 implicit namespace packages, `torch/_C/` is a valid namespace
package even with no `__init__.py`. Python's import system prefers packages
(directories) over modules (`.so` files) of the same name, so `import torch._C`
resolves to the stub-only directory and `_C_for_compiled_check.__file__` is
`None`. torch's `__init__.py` (line 1013) then raises the "Failed to load
PyTorch C extensions" `ImportError` shown above.

This is a torch 2.9.1 + Python 3.14 wheel issue, not user error. The
`JuniperCascor1` env (Python 3.13.13 + torch 2.11.0) was created earlier as
a known-working fallback and has the correct layout — only the `.so` is
present, no shadowing `_C/` directory.

A secondary contributor — the rust_mudgeon `LIBTORCH` / `LD_LIBRARY_PATH`
bleed-through documented in
`juniper-canopy/etc/conda/activate.d/00_isolate_from_tch_rs.sh` — does *not*
fully explain this failure (the wheel-layout error reproduces even with both
vars unset), but it would be a separate import-time failure mode if torch did
load. Both `JuniperCascor` and `JuniperCascor1` now carry matching activate
hooks to defend against it.

---

## 3. Fix

### 3.1 Switch the default cascor env in `juniper_plant_all.bash`

```bash
JUNIPER_CASCOR_CONDA="${JUNIPER_CASCOR_CONDA:-JuniperCascor1}"
```

Mirrors the existing `JUNIPER_CANOPY_CONDA="${JUNIPER_CANOPY_CONDA:-JuniperCanopy1}"`
pattern (canopy hit the LIBTORCH issue weeks earlier and migrated to a
postfixed-`1` env then). Override via `JUNIPER_CASCOR_CONDA=JuniperCascor` if
you have a known-good legacy env.

`JUNIPER_WORKER_CONDA` was also made overridable but its default stays at
`JuniperCascor` — the `juniper-cascor-worker` pip wheel is currently only
installed there. Once the worker is also installed into `JuniperCascor1`,
the worker default can flip too and the legacy env can be retired.

### 3.2 Add LIBTORCH-strip activate hooks to the cascor env

Mirroring `JuniperCanopy1`, two new files were dropped into the JuniperCascor
env tree:

- `/opt/miniforge3/envs/JuniperCascor/etc/conda/activate.d/00_isolate_from_tch_rs.sh`
- `/opt/miniforge3/envs/JuniperCascor/etc/conda/deactivate.d/00_restore_tch_rs.sh`

These strip `LIBTORCH` and any `/rust_mudgeon/` path segments from
`LD_LIBRARY_PATH` on `conda activate`, restoring them on `conda deactivate`,
so the user's `~/.bashrc`-exported `LIBTORCH` does not leak into this env.
**These files live outside the repo** — they are env-local shell hooks,
created the same way `JuniperCanopy1`'s hook was created.

These do *not* fix the wheel-layout issue (the wheel is still broken), but
they preempt the secondary failure mode if a future torch reinstall fixes
the layout while the `~/.bashrc` LIBTORCH export remains.

---

## 4. Verification

After the script change:

```
$ source /opt/miniforge3/etc/profile.d/conda.sh
$ conda activate JuniperCascor1
$ cd juniper-cascor/src
$ JUNIPER_CASCOR_HOST=localhost JUNIPER_CASCOR_PORT=8201 python server.py &
$ curl -fsS http://localhost:8201/v1/health
{"status":"ok","version":"0.4.0"}
```

Server boots cleanly, uvicorn listens on `localhost:8201`, `/v1/health`
returns `{"status":"ok","version":"0.4.0"}` immediately.

---

## 4a. Secondary failure: activate-hook pipefail interaction (2026-05-08)

After §3.1–§3.2 shipped and `juniper-cascor` was confirmed healthy, a
follow-up `juniper_plant_all.bash` run still aborted **silently** during
the `juniper-canopy` activation step. The script log ended at:

```
[juniper_plant_all.bash:439] conda activate "JuniperCanopy1"
```

with `exit_code=1` and no further output (the ERR-trap cleanup message
also did not fire — the shell was already in a corrupted state).

**Reproducer** (run under the same shell flags as the script):

```bash
$ bash -c 'set -euo pipefail
  source /opt/miniforge3/etc/profile.d/conda.sh
  set +u; conda activate JuniperCanopy1; set -u'
/opt/miniforge3/etc/profile.d/conda.sh: line 52: pop_var_context: head of shell_variables not a function context
environment: line 3: pop_var_context: head of shell_variables not a function context
```

**Root cause.** Both LIBTORCH-strip activate hooks
(`/opt/miniforge3/envs/JuniperCanopy1/etc/conda/activate.d/00_isolate_from_tch_rs.sh`
and the `JuniperCascor` mirror added in §3.2) used a pipeline of:

```bash
cleaned=$(printf '%s' "${LD_LIBRARY_PATH}" | tr ':' '\n' | grep -v '/rust_mudgeon/' | paste -sd ':' -)
```

When `LD_LIBRARY_PATH` contains *only* a rust_mudgeon segment — which is
exactly the state set by `~/.bashrc` (`LD_LIBRARY_PATH=${LIBTORCH}/lib:`)
— `grep -v '/rust_mudgeon/'` exits 1 (no matching lines). Under bash's
`pipefail`, the whole pipeline returns 1; under `set -e`, the activate
hook is aborted mid-execution. Conda's variable-context bookkeeping is
left inconsistent, the `pop_var_context` error fires on the next shell
operation that uses scoped variables, and `safe_conda_activate` returns
non-zero. The `juniper_plant_all.bash` ERR trap fires but its cleanup
output is itself swallowed by the corrupted state.

**Fix.** Replaced the `grep -v | paste` pipeline in both hooks with a
pure-bash split that has no subprocess that can fail under pipefail:

```bash
_saved_ifs="${IFS:-$' \t\n'}"
IFS=':' read -ra _segs <<<"${LD_LIBRARY_PATH}"
IFS="${_saved_ifs}"; unset _saved_ifs
cleaned=""
for _seg in "${_segs[@]}"; do
    if [ -n "${_seg}" ] && [[ "${_seg}" != */rust_mudgeon/* ]]; then
        cleaned="${cleaned:+${cleaned}:}${_seg}"
    fi
done
unset _seg _segs
```

Both hooks now safely activate under `set -euo pipefail`. After the
fix, `juniper_plant_all.bash` runs end-to-end with all four services
healthy:

| Service | Port | Health |
|---|---|---|
| juniper-data | 8100 | `{"status":"ok","version":"0.6.0"}` |
| juniper-cascor | 8201 | `{"status":"ok","version":"0.4.0"}` |
| juniper-canopy | 8050 | `{"status":"healthy",…,"juniper_data_available":true}` |
| juniper-cascor-worker | 8210 | `{"status":"ready","service":"juniper-cascor-worker"}` |

These hook files live outside the repo, so the change is documented
here rather than committed. Future env rebuilds should reinstate the
pure-bash split — not the grep pipeline — to keep the hooks safe under
strict callers.

---

## 5. Follow-ups

- **DONE 2026-05-07**: `juniper-cascor-worker` installed editable into
  `JuniperCascor1` from
  `/home/pcalnon/Development/python/Juniper/juniper-cascor-worker`.
  `JUNIPER_WORKER_CONDA` default flipped to `JuniperCascor1` in commit
  `b4fd09d` and the comment block above the assignment was tidied to
  match in this PR. The legacy `JuniperCascor` env is no longer required
  by `juniper_plant_all.bash`.
- **Open**: rebuild or reinstall torch in `JuniperCascor` (or simply
  delete and recreate the env on Python 3.13 to mirror `JuniperCascor1`).
  Until then, `JuniperCascor` remains broken for any cascor module that
  imports torch and should be considered deprecated.
- **Open**: document the env split (or its retirement) in
  `juniper-cascor/AGENTS.md` if useful for future contributors.
