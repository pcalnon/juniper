"""Driver shim that appends --stall-seconds to every run_suite cell invocation.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-10
Status: ad-hoc -- one-off (workaround)
Retire when: run_suite.py grows a first-class stall-seconds passthrough (see below);
             delete with the F-P4-1 re-surface campaign scripts.
Related: F-P4-1 E-A re-surface; the pool>=16 stall class.

WHY THIS EXISTS
---------------
``run_suite.execute_cell`` invokes the driver as a fixed argv::

    [python_bin, driver, "--config", cell_yaml, "--run-dir", run_dir]

with no way to pass ``--stall-seconds``, so every suite cell inherits the driver default
of 120 s. That default is fine while the OUTPUT layer is training (it reports
``current_epoch`` every poll), but during CANDIDATE training no epoch progress is
reported at all -- so a cell whose candidate phase runs longer than 120 s is marked
``stalled`` even though it is healthy and making progress.

E-A's ``candidate_pool_size >= 16`` cells hit exactly that: they stall at ~130 s, twice,
on a clean GPU. The pool 4 / 8 cells finish their candidate phase inside the window and
complete normally, which is why the anomaly tracks pool size and nothing else.

``run_suite`` DOES expose ``JUNIPER_SUITE_DRIVER`` as a documented seam for overriding the
driver path, so this shim forwards to the real driver with the threshold appended --
no change to shipped code. Set ``JUNIPER_EXP_STALL_SECONDS`` to tune (default 900).

The proper fix is a first-class passthrough in ``run_suite`` (ideally an
``execution.stall_seconds`` key beside ``per_run_timeout_seconds``); this unblocks the
re-surface run in the meantime.
"""

import os
import subprocess
import sys
from pathlib import Path

REAL_DRIVER = Path(__file__).resolve().parent.parent / "experiments" / "run_experiment.py"


def main() -> int:
    if not REAL_DRIVER.is_file():
        print(f"shim: real driver not found at {REAL_DRIVER}", file=sys.stderr)
        return 2
    stall = os.environ.get("JUNIPER_EXP_STALL_SECONDS", "900")
    # Caller-supplied args win by position; --stall-seconds is appended, and run_suite
    # never passes it, so there is no duplicate-flag ambiguity.
    argv = [sys.executable, str(REAL_DRIVER), *sys.argv[1:], "--stall-seconds", stall]
    return subprocess.call(argv)


if __name__ == "__main__":
    raise SystemExit(main())
