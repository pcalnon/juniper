#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests -- scheduled Duplicati backup, DB-holder guard
Author:      Paul Calnon
License:     MIT License

Guard 5 of ``util/duplicati_scheduled_backup.bash`` stands the run down when any
live process already has the local Duplicati database open. It exists because
``flock`` only serialises runs started THROUGH that script, while at least three
other paths open the same DB and corrupt it: a hand-started ``duplicati-cli``, the
same invoked by absolute path, and ``duplicati-server`` running the job in-process
from the web UI (which spawns no ``duplicati-cli`` child at all, so no name-anchored
check can see it).

The guard had NO test. That is the dangerous shape for a fail-closed check: if
detection breaks, nothing goes red -- the backup simply proceeds against a database
somebody else is writing, which is the exact corruption the guard was added to
prevent. These tests pin detection itself, not the fast path around it.

``db_holder_pids`` is extracted from the shipped script and evaluated verbatim, so
the tests exercise the real code rather than a copy that can drift.
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - evaluates the repo's OWN extracted shell, fixed argv
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "util" / "duplicati_scheduled_backup.bash"

#: Seconds to wait for the background holder to report that its fd is open.
HOLDER_READY_TIMEOUT = 30.0


def extract_function(name: str) -> str:
    """Return the shell text of ``name`` from the runner, brace-balanced.

    Anchored on the ``name() {`` opener and closed on the first line that is a
    bare ``}`` at column 0 -- the script's own formatting for a top-level
    function. Raises rather than returning a truncated body, so a reformat
    fails loudly here instead of silently testing half a function.
    """
    text = RUNNER.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(name)}\(\) \{{$", text, re.M)
    if m is None:
        raise AssertionError(f"{name}() not found in {RUNNER}")
    lines = text[m.start() :].split("\n")
    for i, line in enumerate(lines[1:], start=1):
        if line == "}":
            return "\n".join(lines[: i + 1])
    raise AssertionError(f"{name}() has no closing brace at column 0")


def holder_pids(dbpath: str) -> list[str]:
    """Run the REAL db_holder_pids() against ``dbpath`` and return the pids."""
    script = textwrap.dedent("""\
        set -euo pipefail
        DBPATH="$1"
        %s
        db_holder_pids
        """) % extract_function("db_holder_pids")
    proc = subprocess.run(  # nosec B603 - fixed argv, repo's own shell
        ["bash", "-c", script, "bash", dbpath],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"db_holder_pids failed: {proc.stderr}"
    return [ln for ln in proc.stdout.split("\n") if ln.strip()]


class _Holder:
    """A background process holding an fd open on ``path``."""

    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self) -> subprocess.Popen:
        Path(self.path).touch()
        self.proc = subprocess.Popen(  # nosec B603 - fixed argv
            [sys.executable, "-c", "import sys,time; f=open(sys.argv[1],'r+b'); print('ready', flush=True); time.sleep(600)", self.path],
            stdout=subprocess.PIPE,
            text=True,
        )
        deadline = time.time() + HOLDER_READY_TIMEOUT
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if line.strip() == "ready":
                return self.proc
            if self.proc.poll() is not None:
                raise AssertionError("holder exited before signalling ready")
        raise AssertionError("holder never signalled ready")

    def __exit__(self, *exc) -> None:
        self.proc.kill()
        self.proc.wait(timeout=30)
        if self.proc.stdout is not None:
            self.proc.stdout.close()


@unittest.skipUnless(sys.platform.startswith("linux"), "reads /proc")
class TestDbHolderGuard(unittest.TestCase):
    def test_a_live_holder_is_detected(self) -> None:
        """The load-bearing arm. If this regresses, the guard passes on a DB
        somebody else is writing and the corruption it exists to stop happens
        silently."""
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "local.sqlite")
            with _Holder(db) as proc:
                self.assertEqual(holder_pids(db), [str(proc.pid)])

    def test_no_holder_is_an_empty_result(self) -> None:
        """The control: an unheld database must not report a holder, or every
        run would stand down forever."""
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "local.sqlite")
            Path(db).touch()
            self.assertEqual(holder_pids(db), [])

    def test_a_symlinked_dbpath_still_finds_the_holder(self) -> None:
        """/proc/<pid>/fd/<n> is stored fully resolved by the kernel, so DBPATH
        has to be resolved before comparison. Comparing a resolved fd target
        against DBPATH verbatim matched NOTHING whenever DBPATH reached the
        database through a symlinked directory -- detection failed open."""
        with tempfile.TemporaryDirectory() as tmp:
            real_dir = os.path.join(tmp, "real")
            os.mkdir(real_dir)
            os.symlink(real_dir, os.path.join(tmp, "link"))
            real_db = os.path.join(real_dir, "local.sqlite")
            via_link = os.path.join(tmp, "link", "local.sqlite")
            with _Holder(real_db) as proc:
                self.assertIn(str(proc.pid), holder_pids(via_link))

    def test_the_scan_reports_only_foreign_holders(self) -> None:
        """No self-pid leaks into a normal call.

        The `$$` skip in the function is PARTIAL by construction -- the trailing
        `| sort -u` and the process substitution each run in a subshell that
        inherits the caller's descriptors, and `$$` names only the main shell. It
        has always been so (verified 2026-08-29: the previous implementation
        reports the same subshell pids). It is harmless because the runner never
        opens the database itself -- Guard 4 puts the LOCK file on fd 9, not the
        DB -- so at the call site no descriptor on DBPATH exists to inherit. This
        test pins that real-world shape: with one foreign holder, the answer is
        that holder and nothing else.
        """
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "local.sqlite")
            with _Holder(db) as proc:
                self.assertEqual(holder_pids(db), [str(proc.pid)])

    def test_the_runner_never_opens_the_database_itself(self) -> None:
        """The premise the partial `$$` skip rests on. Guard 4 redirects fd 9 to
        the lock file; if a future edit pointed a descriptor at DBPATH instead,
        the guard would start reporting the runner's own subshells and stand
        every run down."""
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('exec 9>"${LOCK_FILE}"', text)
        self.assertNotRegex(text, r'exec\s+\d+[<>]+"?\$\{DBPATH\}', "the runner must not hold DBPATH open itself")


class TestDbHolderImplementation(unittest.TestCase):
    def test_the_scan_does_not_fork_per_file_descriptor(self) -> None:
        """A `readlink` per fd on the HOST cost 59.17 s at 10,211 open fds
        (measured 2026-08-29) -- paid on every run, before any backup work, and
        scaling with the machine rather than with the backup. Pin the shape so
        the loop cannot come back."""
        body = extract_function("db_holder_pids")
        self.assertNotIn("for fd in /proc/", body, "per-fd shell loop reintroduced")
        self.assertIn("find /proc/", body, "the single-find scan is gone")
        self.assertIn("-printf", body, "find must report targets itself, not via a readlink fork")

    def test_dbpath_is_resolved_before_comparison(self) -> None:
        body = extract_function("db_holder_pids")
        self.assertRegex(body, r'readlink -f "\$\{DBPATH\}"', "DBPATH must be resolved or a symlinked configuration matches nothing")

    def test_pgrep_is_not_used(self) -> None:
        """`pgrep -f` self-matches, and a name check cannot see duplicati-server
        running the job in-process."""
        self.assertNotIn("pgrep", extract_function("db_holder_pids"))


if __name__ == "__main__":
    unittest.main()
