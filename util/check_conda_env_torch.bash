#!/usr/bin/env bash
#
# check_conda_env_torch.bash — diagnose the torch._C shadow described
# in notes/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md (P-5).
#
# Exit codes:
#   0 — env is healthy: regular CPython, torch imports, _C resolves to
#       the .so (not the directory).
#   1 — env not found.
#   2 — interpreter is free-threaded (cp*t ABI) but torch wheel is
#       cp* (no t). The shadow case.
#   3 — torch import fails for some other reason.
#   4 — torch._C resolves to a directory (namespace package), not a .so.
#
# Usage:
#   util/check_conda_env_torch.bash JuniperCascor
#   util/check_conda_env_torch.bash JuniperCanopy
#   util/check_conda_env_torch.bash JuniperCascor1
#
# Environment:
#   JUNIPER_CONDA_DIR — conda/miniforge root (default: /opt/miniforge3)
#
set -u

ENV_NAME="${1:-}"
if [[ -z "$ENV_NAME" ]]; then
    echo "usage: $0 <conda-env-name>" >&2
    exit 1
fi

# Override for hermetic tests / non-default installs (matches plant/isolated JUNIPER_*_CONDA_DIR pattern).
CONDA_DIR="${JUNIPER_CONDA_DIR:-/opt/miniforge3}"
ENV_PATH="${CONDA_DIR}/envs/$ENV_NAME"
PYTHON="$ENV_PATH/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "::error::env $ENV_NAME not found at $ENV_PATH" >&2
    exit 1
fi

echo "═══ env: $ENV_NAME ═══"

# 1. Interpreter ABI tag.
ABI=$("$PYTHON" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')
echo "interpreter EXT_SUFFIX: $ABI"
if [[ "$ABI" == *"-cp"*"t-"* || "$ABI" == *"t-x86_64"* ]]; then
    echo "::warning::interpreter is free-threaded (cp*t ABI)"
    INTERP_FT=1
else
    INTERP_FT=0
fi

# 2. torch import.
if ! "$PYTHON" -c 'import torch' 2>/dev/null; then
    echo "::error::torch import fails"
    "$PYTHON" -c 'import torch' 2>&1 | tail -8 | sed 's/^/    /'

    # Distinguish the shadow case from generic import failures by
    # inspecting the filesystem directly (find_spec triggers torch's
    # own import-error path, so we can't ask Python for the origin).
    # Scan every site-packages dir under the env — under FT envs,
    # sys.path includes both python3.14t/site-packages and a fallback
    # python3.14/site-packages, and torch typically lives in the
    # latter.
    while IFS= read -r torch_dir; do
        if [[ -d "$torch_dir/_C" ]]; then
            SO_COUNT=$(find "$torch_dir" -maxdepth 1 -name '_C.cpython-*.so' | wc -l)
            SO_TAGS=$(find "$torch_dir" -maxdepth 1 -name '_C.cpython-*.so' -printf '%f ')
            echo "::error::torch._C/ namespace-package directory present at $torch_dir/_C"
            echo "::error::torch _C.so files alongside it: $SO_COUNT ($SO_TAGS)"
            echo "          See notes/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md for recovery."
            if [[ "$INTERP_FT" == "1" ]]; then
                exit 2  # FT shadow — most common case
            fi
            exit 4
        fi
    done < <(find "$ENV_PATH" -maxdepth 5 -type d -name torch 2>/dev/null)
    exit 3
fi

VERSION=$("$PYTHON" -c 'import torch; print(torch.__version__)')
LOC=$("$PYTHON" -c 'import torch._C as c; print(getattr(c, "__file__", "<no __file__>"))')
echo "torch version: $VERSION"
echo "torch._C origin: $LOC"

if [[ "$LOC" == *"<no __file__>"* ]]; then
    echo "::error::torch._C has no __file__ — namespace-package shadow"
    exit 4
fi

echo "::notice::env $ENV_NAME healthy"
exit 0
