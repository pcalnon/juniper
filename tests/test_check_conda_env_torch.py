"""
Tests for util/check_conda_env_torch.bash

Hermetic coverage for the P-5 torch._C shadow diagnostic
(``notes/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md``).

The script classifies conda envs into exit codes 0/1/2/3/4 (healthy / missing /
FT-shadow / other-import-fail / namespace-package). A misclassification sends
operators down the wrong recovery path. Prior suite had zero behavioral
coverage; these cases drive a stub ``bin/python`` under ``JUNIPER_CONDA_DIR``
with staged site-packages layouts — no real conda or torch.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "check_conda_env_torch.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 15


def _write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    path.chmod(0o755)


class TorchEnvFixture:
    """Synthetic conda root with a stub python and optional torch layouts."""

    def __init__(
        self,
        tmpdir: str,
        *,
        env_name: str = "JuniperCascor1",
        abi: str = ".cpython-314-x86_64-linux-gnu.so",
        import_torch: str = "ok",
        version: str = "2.6.0",
        c_file: str = "/fake/site-packages/torch/_C.cpython-314-x86_64-linux-gnu.so",
        create_python: bool = True,
    ):
        self.root = Path(tmpdir)
        self.env_name = env_name
        self.env_path = self.root / "envs" / env_name
        self.site = self.env_path / "lib" / "python3.14" / "site-packages"
        if create_python:
            self._write_python(
                abi=abi,
                import_torch=import_torch,
                version=version,
                c_file=c_file,
            )

    def _write_python(self, *, abi: str, import_torch: str, version: str, c_file: str) -> None:
        # Stub switches on the exact ``-c`` snippets the script issues.
        _write_executable(
            self.env_path / "bin" / "python",
            f"""
            #!/usr/bin/env bash
            if [[ "$1" != "-c" ]]; then
                echo "unexpected argv: $*" >&2
                exit 99
            fi
            code="$2"
            case "$code" in
                *'sysconfig.get_config_var("EXT_SUFFIX")'*)
                    echo '{abi}'
                    exit 0
                    ;;
                *'import torch; print(torch.__version__)'*)
                    echo '{version}'
                    exit 0
                    ;;
                *'import torch._C as c'*)
                    echo '{c_file}'
                    exit 0
                    ;;
                *'import torch'*)
                    if [[ "{import_torch}" == "ok" ]]; then
                        exit 0
                    fi
                    echo "ImportError: stub torch import fail" >&2
                    exit 1
                    ;;
            esac
            echo "unhandled -c: $code" >&2
            exit 98
            """,
        )

    def stage_torch_shadow(self, *, with_so: bool = True) -> Path:
        torch_dir = self.site / "torch"
        (torch_dir / "_C").mkdir(parents=True)
        if with_so:
            (torch_dir / "_C.cpython-314-x86_64-linux-gnu.so").write_text("", encoding="utf-8")
        return torch_dir

    def env(self) -> dict[str, str]:
        env = RedactedEnv(os.environ)
        env["JUNIPER_CONDA_DIR"] = str(self.root)
        return env


def _run(fixture: TorchEnvFixture, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=fixture.env(),
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestCheckCondaEnvTorch(unittest.TestCase):
    """Exit-code matrix for the P-5 torch._C shadow diagnostic."""

    def test_usage_without_env_name_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(tmp, create_python=False)
            result = _run(fixture)
            self.assertEqual(result.returncode, 1)
            self.assertIn("usage:", result.stderr)

    def test_missing_env_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(tmp, create_python=False)
            result = _run(fixture, "NoSuchEnv")
            self.assertEqual(result.returncode, 1)
            self.assertIn("::error::env NoSuchEnv not found", result.stderr)

    def test_healthy_env_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(tmp, import_torch="ok")
            result = _run(fixture, fixture.env_name)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("::notice::env JuniperCascor1 healthy", result.stdout)
            self.assertIn("torch version: 2.6.0", result.stdout)

    def test_ft_shadow_exits_two(self) -> None:
        # Free-threaded ABI + torch/_C dir + .so alongside → exit 2 (FT shadow).
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(
                tmp,
                abi=".cpython-314t-x86_64-linux-gnu.so",
                import_torch="fail",
            )
            fixture.stage_torch_shadow(with_so=True)
            result = _run(fixture, fixture.env_name)
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("::warning::interpreter is free-threaded", result.stdout)
            self.assertIn("::error::torch import fails", result.stdout)
            self.assertIn("torch._C/ namespace-package directory present", result.stdout)

    def test_non_ft_namespace_dir_exits_four(self) -> None:
        # Regular ABI + torch/_C dir (no FT) → exit 4, not the FT-shadow code.
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(
                tmp,
                abi=".cpython-314-x86_64-linux-gnu.so",
                import_torch="fail",
            )
            fixture.stage_torch_shadow(with_so=True)
            result = _run(fixture, fixture.env_name)
            self.assertEqual(result.returncode, 4, msg=result.stderr + result.stdout)
            self.assertNotIn("::warning::interpreter is free-threaded", result.stdout)
            self.assertIn("torch._C/ namespace-package directory present", result.stdout)

    def test_other_import_failure_exits_three(self) -> None:
        # Import fails and no torch/_C directory on disk → generic exit 3.
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(tmp, import_torch="fail")
            result = _run(fixture, fixture.env_name)
            self.assertEqual(result.returncode, 3, msg=result.stderr + result.stdout)
            self.assertIn("::error::torch import fails", result.stdout)

    def test_imported_torch_without_c_file_exits_four(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TorchEnvFixture(
                tmp,
                import_torch="ok",
                c_file="<no __file__>",
            )
            result = _run(fixture, fixture.env_name)
            self.assertEqual(result.returncode, 4, msg=result.stderr + result.stdout)
            self.assertIn("torch._C has no __file__", result.stdout)

    def test_default_conda_dir_and_override_seam(self) -> None:
        # Drift guard: default stays /opt/miniforge3; JUNIPER_CONDA_DIR is the override.
        self.assertIn('CONDA_DIR="${JUNIPER_CONDA_DIR:-/opt/miniforge3}"', SCRIPT_TEXT)
        self.assertIn('ENV_PATH="${CONDA_DIR}/envs/$ENV_NAME"', SCRIPT_TEXT)


if __name__ == "__main__":
    unittest.main()
