"""Tests for the AST symbol-loss screen (``symbol_loss_check`` + its CLI).

Migrated from juniper-ml's ``tests/test_symbol_loss_check.py`` (Wave 0 of the
sequence-safety rollout) and converted from importlib path-loading of the util
script to package imports + in-process CLI invocation. The CLI is driven
in-process (``cli_main(argv)`` with ``redirect_stdout``) -- the ci-tools house
idiom (see ``test_env_drift_check.py``) -- so the ``--enforce`` per-file coverage
gate measures the modules (a subprocess-driven CLI would not be captured by
``--cov``); a single ``python -m`` ``--help`` smoke proves the module-form entry.

Hermetic: every case builds a throwaway git repo under a tempdir (``git -C``,
never ``cd``) with a BASE and a HEAD commit. The fixtures pin ``user.name`` /
``user.email`` / ``commit.gpgsign`` repo-locally and the module only *reads* git
(rev-parse / cat-file / diff / log), so nothing signs and no custom subprocess
``env=`` mapping is needed (the RedactedEnv house rule applies only to raw
``os.environ`` mappings, of which there are none here).

Coverage: clean pass, LOST detection (same-file), the SF3 bare-name masking pin,
qualified-name + body-similarity relocation, the WEAKENED threshold arms,
DUPLICATED, the ``@property``/``@x.setter`` accessor-pair guard, import/const
advisory WARN, bash LOST-FAIL / WEAKENED-WARN, the ``Allow-Symbol-Loss`` trailer
escape + wildcard rejection, unparseable-blob notes, human + JSON output, the
``--advisory`` downgrade, exit codes 0/1/2, and the new ``--scope`` glob
parameterization (default==historical predicate; a glob screens its surface; the
extension gate still applies; ``--files`` still bypasses scope) + ``_match_scope``.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import juniper_ci_tools.symbol_loss_check as slc
from juniper_ci_tools.cli_symbol_loss_check import main as cli_main

_TIMEOUT = 30
_CI_TOOLS_ROOT = Path(__file__).resolve().parent.parent


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check, timeout=_TIMEOUT)


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "Test User")
    _git(root, "config", "commit.gpgsign", "false")


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _commit(root: Path, msg: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)


def _invoke(root: Path, *extra: str, base: str = "HEAD~1", head: str = "HEAD") -> tuple[int, str, str]:
    """Drive the CLI in-process; return (exit_code, stdout, stderr)."""
    argv = ["--base", base, "--head", head, "--repo-root", str(root), *extra]
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli_main(argv)
    return rc, out.getvalue(), err.getvalue()


def _run_json(root: Path, *extra: str, base: str = "HEAD~1", head: str = "HEAD") -> tuple[int, dict, str]:
    rc, out, err = _invoke(root, "--json", *extra, base=base, head=head)
    return rc, json.loads(out), err


def _by_symbol(report: dict) -> dict:
    return {f["symbol"]: f for f in report["findings"]}


class SymbolLossBehaviourTest(unittest.TestCase):
    """End-to-end verdicts against real git fixture repos (default scope)."""

    def test_additions_only_is_clean(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n\n    def b(self):\n        return 2\n")
            _commit(root, "add method b")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["fail_count"], 0)

    def test_new_file_addition_is_clean(self) -> None:
        """A brand-new screened file (absent at base) yields no LOST -- covers the
        base-blob-absent branch."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            _write(root, "util/brand_new.py", "def fresh():\n    return 1\n")
            _commit(root, "add a new util module")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["fail_count"], 0)

    def test_same_file_method_deletion_is_lost_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n\n    def drop_me(self):\n        return 2\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n")
            _commit(root, "drop drop_me")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            f = _by_symbol(report).get("method:TestX.drop_me")
            self.assertIsNotNone(f, msg=report)
            self.assertEqual((f["verdict"], f["severity"]), ("LOST", "FAIL"))

    def test_bare_name_collision_does_not_mask_a_real_deletion(self) -> None:
        """SF3 pin: deleting TestA.test_default while an unrelated TestB.test_default
        exists must still FAIL on the qualified key -- never masked by the bare name."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(
                root,
                "tests/test_x.py",
                "class TestA:\n    def test_default(self):\n        assert 1\n\n\nclass TestB:\n    def test_default(self):\n        assert 2\n",
            )
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestA:\n    pass\n\n\nclass TestB:\n    def test_default(self):\n        assert 2\n")
            _commit(root, "drop TestA.test_default")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            by = _by_symbol(report)
            self.assertIn("method:TestA.test_default", by)
            self.assertEqual(by["method:TestA.test_default"]["severity"], "FAIL")
            self.assertNotIn("method:TestB.test_default", by)

    def test_qualified_relocation_is_warn_not_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_a.py", "class TestA:\n    def moved(self):\n        assert 1\n        assert 2\n        assert 3\n")
            _write(root, "tests/test_b.py", "class TestB:\n    def other(self):\n        return 0\n")
            _commit(root, "base")
            _write(root, "tests/test_a.py", "class TestA:\n    pass\n")
            _write(
                root,
                "tests/test_b.py",
                "class TestB:\n    def other(self):\n        return 0\n\n\nclass TestA:\n    def moved(self):\n        assert 1\n        assert 2\n        assert 3\n",
            )
            _commit(root, "relocate TestA.moved a->b")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            f = _by_symbol(report).get("method:TestA.moved")
            self.assertIsNotNone(f, msg=report)
            self.assertEqual((f["verdict"], f["severity"]), ("RELOCATED", "WARN"))
            self.assertEqual(f["detail"]["match"], "qualified-name")

    def test_weakened_shrink_past_threshold_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def big():\n    a = 1\n    b = 2\n    c = 3\n    d = 4\n    e = 5\n    return a + b + c + d + e\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def big():\n    return 0\n")
            _commit(root, "gut big")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            f = _by_symbol(report).get("func:big")
            self.assertIsNotNone(f, msg=report)
            self.assertEqual((f["verdict"], f["severity"]), ("WEAKENED", "FAIL"))

    def test_small_shrink_below_threshold_is_not_flagged(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def f():\n    a = 1\n    b = 2\n    return a + b\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def f():\n    a = 1\n    return a\n")
            _commit(root, "minor edit")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertNotIn("func:f", _by_symbol(report))

    def test_same_length_gutting_is_invisible_blind_spot(self) -> None:
        """Documented WEAKENED blind spot: a same-line-count body swap has delta 0."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def f():\n    a = compute_real_thing()\n    b = another_real_thing()\n    return a + b\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def f():\n    a = 0\n    b = 0\n    return a + b\n")
            _commit(root, "gut but keep line count")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertNotIn("func:f", _by_symbol(report))

    def test_duplicated_definition_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def dup():\n    return 1\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def dup():\n    return 1\n\n\ndef dup():\n    return 2\n")
            _commit(root, "fuse a duplicate dup")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            f = _by_symbol(report).get("func:dup")
            self.assertIsNotNone(f, msg=report)
            self.assertEqual((f["verdict"], f["severity"]), ("DUPLICATED", "FAIL"))

    def test_property_setter_pair_is_not_false_duplicated(self) -> None:
        """Accessor-pair guard (``_accessor_suffix``): a ``@property`` getter and its
        ``@x.setter`` share a method name but are keyed distinctly, so an unchanged
        accessor pair is NEVER a false DUPLICATED -- while a genuine same-name method
        re-definition still DUPLICATEs."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            base = "class C:\n    @property\n    def value(self):\n        return self._v\n\n    @value.setter\n    def value(self, v):\n        self._v = v\n\n    def plain(self):\n        return 1\n"
            _write(root, "util/acc.py", base)
            _commit(root, "base")
            head = base + "\n    def plain(self):\n        return 2\n"
            _write(root, "util/acc.py", head)
            _commit(root, "redefine plain (real dup), keep the property/setter pair")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            by = _by_symbol(report)
            self.assertNotIn("method:C.value", by, msg=report)
            self.assertNotIn("method:C.value.setter", by, msg=report)
            dup = by.get("method:C.plain")
            self.assertIsNotNone(dup, msg=report)
            self.assertEqual((dup["verdict"], dup["severity"]), ("DUPLICATED", "FAIL"))

    def test_removed_import_and_const_are_advisory_warn(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "import os\n\nFOO = 1\n\n\ndef keep():\n    return FOO\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 1\n")
            _commit(root, "drop import + const")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            by = _by_symbol(report)
            self.assertEqual(by["import:os"]["severity"], "WARN")
            self.assertEqual(by["const:FOO"]["severity"], "WARN")

    def test_bash_function_deletion_is_lost_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo foo\n}\n\nbar() {\n    echo bar\n}\n")
            _commit(root, "base")
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo foo\n}\n")
            _commit(root, "drop bar")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            f = _by_symbol(report).get("fn:bar")
            self.assertIsNotNone(f, msg=report)
            self.assertEqual((f["verdict"], f["severity"]), ("LOST", "FAIL"))

    def test_bash_weakened_is_warn_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo 1\n    echo 2\n    echo 3\n    echo 4\n    echo 5\n    echo 6\n}\n")
            _commit(root, "base")
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo 1\n}\n")
            _commit(root, "gut foo")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            f = _by_symbol(report).get("fn:foo")
            if f is not None:
                self.assertEqual(f["severity"], "WARN")

    def test_deleted_file_flags_every_definition(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_gone.py", "class TestGone:\n    def a(self):\n        return 1\n\n    def b(self):\n        return 2\n")
            _write(root, "tests/test_stay.py", "class TestStay:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            (root / "tests" / "test_gone.py").unlink()
            _commit(root, "delete whole test file")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            by = _by_symbol(report)
            self.assertEqual(by["method:TestGone.a"]["verdict"], "LOST")
            self.assertEqual(by["method:TestGone.b"]["verdict"], "LOST")


class SymbolLossScopeTest(unittest.TestCase):
    """The new --scope glob parameterization + the default back-compat."""

    def test_default_scope_ignores_out_of_scope_source(self) -> None:
        """With no --scope, a deletion under src/ (an application-source tree) is NOT
        screened -- the historical juniper-ml predicate is preserved verbatim."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "src/pkg/mod.py", "def keep():\n    return 1\n\n\ndef drop_me():\n    return 2\n")
            _commit(root, "base")
            _write(root, "src/pkg/mod.py", "def keep():\n    return 1\n")
            _commit(root, "drop drop_me under src/")
            rc, report, err = _run_json(root)  # no --scope
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["files_screened"], 0)

    def test_scope_glob_screens_matched_surface(self) -> None:
        """--scope 'src/**/*.py' screens a deletion under src/ (incl. nested) but a
        util/ deletion outside the glob is not screened."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "src/pkg/mod.py", "def keep():\n    return 1\n\n\ndef drop_me():\n    return 2\n")
            _write(root, "util/other.py", "def util_keep():\n    return 1\n\n\ndef util_drop():\n    return 2\n")
            _commit(root, "base")
            _write(root, "src/pkg/mod.py", "def keep():\n    return 1\n")
            _write(root, "util/other.py", "def util_keep():\n    return 1\n")
            _commit(root, "drop under both trees")
            rc, report, err = _run_json(root, "--scope", "src/**/*.py")
            self.assertEqual(rc, 1, msg=err)
            by = _by_symbol(report)
            self.assertIn("func:drop_me", by)
            self.assertEqual(by["func:drop_me"]["verdict"], "LOST")
            # util/other.py is outside the glob -> not screened, so util_drop is invisible.
            self.assertNotIn("func:util_drop", by)
            self.assertIn("util/other.py", report["stats"]["skipped_out_of_scope"])

    def test_scope_matches_top_of_tree_file(self) -> None:
        """'src/**/*.py' matches a .py directly under src/ (the **/-is-zero-segments arm)."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "src/top.py", "def keep():\n    return 1\n\n\ndef drop_me():\n    return 2\n")
            _commit(root, "base")
            _write(root, "src/top.py", "def keep():\n    return 1\n")
            _commit(root, "drop drop_me at src top")
            rc, report, err = _run_json(root, "--scope", "src/**/*.py")
            self.assertEqual(rc, 1, msg=err)
            self.assertIn("func:drop_me", _by_symbol(report))

    def test_scope_extension_gate_still_applies(self) -> None:
        """A path matching the glob but without a screenable extension is not screened."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "src/data.json", '{"a": 1, "b": 2, "c": 3}\n')
            _write(root, "src/mod.py", "def keep():\n    return 1\n\n\ndef drop_me():\n    return 2\n")
            _commit(root, "base")
            _write(root, "src/data.json", '{"a": 1}\n')
            _write(root, "src/mod.py", "def keep():\n    return 1\n")
            _commit(root, "trim json + drop a def")
            rc, report, err = _run_json(root, "--scope", "src/**")
            self.assertEqual(rc, 1, msg=err)
            # the .py under the glob screens; the .json is gated out by the extension check.
            self.assertIn("func:drop_me", _by_symbol(report))
            self.assertIn("src/data.json", report["stats"]["skipped_out_of_scope"])

    def test_multiple_scope_globs_are_union(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "a/x.py", "def keep():\n    return 1\n\n\ndef drop_a():\n    return 2\n")
            _write(root, "b/y.py", "def keep2():\n    return 1\n\n\ndef drop_b():\n    return 2\n")
            _commit(root, "base")
            _write(root, "a/x.py", "def keep():\n    return 1\n")
            _write(root, "b/y.py", "def keep2():\n    return 1\n")
            _commit(root, "drop in both a and b")
            rc, report, err = _run_json(root, "--scope", "a/**/*.py", "--scope", "b/**/*.py")
            self.assertEqual(rc, 1, msg=err)
            by = _by_symbol(report)
            self.assertIn("func:drop_a", by)
            self.assertIn("func:drop_b", by)


class SymbolLossEscapeHatchTest(unittest.TestCase):
    """The Allow-Symbol-Loss commit-trailer escape + wildcard rejection."""

    def test_trailer_waives_enumerated_symbol(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef stays():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def stays():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: gone")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            f = _by_symbol(report).get("func:gone")
            self.assertIsNotNone(f, msg=report)
            self.assertEqual((f["verdict"], f["severity"]), ("WAIVED", "WAIVED"))

    def test_trailer_accepts_kind_qualified_form(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: func:gone")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(_by_symbol(report)["func:gone"]["severity"], "WAIVED")

    def test_wildcard_trailer_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: *")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 1, msg=err)
            self.assertTrue(report["stats"]["wildcard_rejected"])
            self.assertEqual(_by_symbol(report)["func:gone"]["severity"], "FAIL")


class SymbolLossHumanOutputTest(unittest.TestCase):
    """The non-JSON human reporter (``_print_human``) branches."""

    def test_human_clean_prints_ok(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def a():\n    return 1\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def a():\n    return 1\n\n\ndef b():\n    return 2\n")
            _commit(root, "add b")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("OK: no unwaived symbol-loss findings", out)

    def test_human_fail_lists_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def keep():\n    return 1\n\n\ndef gone():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 1\n")
            _commit(root, "drop gone")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 1, msg=err)
            self.assertIn("[FAIL/LOST]", out)
            self.assertIn("FAIL: 1 unwaived symbol-loss finding", out)

    def test_human_waived_and_wildcard_notes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: gone\nAllow-Symbol-Loss: *")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("waived (Allow-Symbol-Loss): gone", out)
            self.assertIn("REJECTED", out)

    def test_human_unparseable_head_note(self) -> None:
        """A syntax-broken HEAD blob is surfaced as an unparseable-blob note; its base
        symbols read as LOST (head inventory is empty)."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def keep():\n    return 1\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep(:\n    return 1\n")  # deliberate syntax error
            _commit(root, "break the syntax")
            rc, out, err = _invoke(root)
            self.assertEqual(rc, 1, msg=err)
            self.assertIn("unparseable blobs", out)

    def test_unparseable_base_blob_yields_no_false_lost(self) -> None:
        """A syntax-broken BASE blob contributes no base inventory -> no false LOST."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def keep(:\n    return 1\n")  # broken at base
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 1\n")  # fixed at head
            _commit(root, "fix the syntax")
            rc, report, err = _run_json(root)
            self.assertEqual(rc, 0, msg=err)
            self.assertEqual(report["stats"]["fail_count"], 0)
            self.assertTrue(any("util/h.py" in b for b in report["stats"]["unparseable_blobs"]))


class SymbolLossCliContractTest(unittest.TestCase):
    """Exit-code + argument contract."""

    def test_missing_base_is_usage_error(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            cli_main(["--head", "HEAD"])
        self.assertEqual(ctx.exception.code, 2)

    def test_unresolvable_ref_is_exit_2(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            rc, out, err = _invoke(root, base="does-not-exist", head="HEAD")
            self.assertEqual(rc, 2)
            self.assertIn("could not resolve ref", err)

    def test_explicit_files_bypasses_scope_filter(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "scripts/tool.py", "def helper():\n    return 1\n")
            _commit(root, "base")
            _write(root, "scripts/tool.py", "x = 1\n")
            _commit(root, "drop helper")
            rc_auto, report_auto, err_auto = _run_json(root)
            self.assertEqual(rc_auto, 0, msg=err_auto)  # scripts/ excluded by default
            rc_x, report_x, err_x = _run_json(root, "--files", "scripts/tool.py")
            self.assertEqual(rc_x, 1, msg=err_x)
            self.assertEqual(_by_symbol(report_x)["func:helper"]["verdict"], "LOST")

    def test_module_form_help_smoke(self) -> None:
        """`python -m juniper_ci_tools.cli_symbol_loss_check --help` resolves and shows
        --scope (the module-form entry the rollout plan names). cwd is the ci-tools root
        so it works whether or not the package is pip-installed."""
        cp = subprocess.run(
            [sys.executable, "-m", "juniper_ci_tools.cli_symbol_loss_check", "--help"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            cwd=str(_CI_TOOLS_ROOT),
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("--scope", cp.stdout)


class SymbolLossAdvisoryTest(unittest.TestCase):
    """The --advisory (per-PR allow-symbol-loss label hatch) exit-0 downgrade."""

    def test_advisory_downgrades_fail_to_exit_0_but_keeps_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n\n    def drop_me(self):\n        return 2\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n")
            _commit(root, "drop drop_me")
            rc_strict, report_strict, err_strict = _run_json(root)
            self.assertEqual(rc_strict, 1, msg=err_strict)
            rc_adv, report_adv, err_adv = _run_json(root, "--advisory")
            self.assertEqual(rc_adv, 0, msg=err_adv)
            self.assertTrue(report_adv["advisory"])
            f = _by_symbol(report_adv).get("method:TestX.drop_me")
            self.assertIsNotNone(f, msg=report_adv)
            self.assertEqual((f["verdict"], f["severity"]), ("LOST", "FAIL"))
            self.assertEqual(report_adv["stats"]["fail_count"], 1)

    def test_advisory_human_output_prints_downgrade_note(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone")
            rc, out, err = _invoke(root, "--advisory")
            self.assertEqual(rc, 0, msg=err)
            self.assertIn("ADVISORY", out)

    def test_advisory_clean_diff_is_still_exit_0(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n\n    def b(self):\n        return 2\n")
            _commit(root, "add method b")
            rc, report, err = _run_json(root, "--advisory")
            self.assertEqual(rc, 0, msg=err)
            self.assertTrue(report["advisory"])
            self.assertEqual(report["stats"]["fail_count"], 0)

    def test_advisory_does_not_mask_invocation_error_exit_2(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            rc, out, err = _invoke(root, "--advisory", base="does-not-exist", head="HEAD")
            self.assertEqual(rc, 2, msg=out)


class SymbolLossHelperUnitTest(unittest.TestCase):
    """Direct unit tests for the pure helpers (package import)."""

    def test_in_scope(self) -> None:
        self.assertTrue(slc.in_scope("tests/test_x.py"))
        self.assertTrue(slc.in_scope("util/a/b.py"))
        self.assertTrue(slc.in_scope("util/s.bash"))
        self.assertFalse(slc.in_scope("tests/sub/test_x.py"))  # nested tests/ subdir
        self.assertFalse(slc.in_scope("scripts/x.py"))
        self.assertFalse(slc.in_scope("juniper-ci-tools/src/x.py"))
        self.assertFalse(slc.in_scope("docs/x.md"))

    def test_match_scope(self) -> None:
        # ** recursion, incl. the zero-segment arm (src/foo.py) and nesting.
        self.assertTrue(slc._match_scope("src/foo.py", ["src/**/*.py"]))
        self.assertTrue(slc._match_scope("src/tests/a.py", ["src/**/*.py"]))
        self.assertFalse(slc._match_scope("util/a.py", ["src/**/*.py"]))
        # single * stays within one segment.
        self.assertTrue(slc._match_scope("tests/a.py", ["tests/*.py"]))
        self.assertFalse(slc._match_scope("tests/sub/a.py", ["tests/*.py"]))
        # trailing ** matches anything under a prefix.
        self.assertTrue(slc._match_scope("util/a/b.bash", ["util/**"]))
        # ? is a single non-/ char; a literal glob is an exact match.
        self.assertTrue(slc._match_scope("a1b.py", ["a?b.py"]))
        self.assertFalse(slc._match_scope("a/b.py", ["a?b.py"]))
        self.assertTrue(slc._match_scope("AGENTS.md", ["AGENTS.md"]))
        # union across globs; empty glob list matches nothing.
        self.assertTrue(slc._match_scope("b/y.py", ["a/**", "b/**"]))
        self.assertFalse(slc._match_scope("src/foo.py", []))

    def test_py_symbols_qualifies_methods(self) -> None:
        syms = slc.py_symbols("class A:\n    def m(self):\n        return 1\n\n\ndef f():\n    return 2\n")
        self.assertIn("class:A", syms)
        self.assertIn("method:A.m", syms)
        self.assertIn("func:f", syms)

    def test_py_symbols_tuple_and_ann_assign_consts(self) -> None:
        syms = slc.py_symbols("A, B = 1, 2\nC: int = 3\n")
        self.assertIn("const:A", syms)
        self.assertIn("const:B", syms)
        self.assertIn("const:C", syms)

    def test_py_symbols_returns_none_on_syntax_error(self) -> None:
        self.assertIsNone(slc.py_symbols("def broken(:\n"))

    def test_bash_symbols_function_keyword_form(self) -> None:
        syms = slc.bash_symbols("function foo {\n    echo 1\n}\n\nbar() {\n    echo 2\n}\n")
        self.assertIn("fn:foo", syms)
        self.assertIn("fn:bar", syms)

    def test_parse_allow_trailers_enumerates_and_flags_wildcard(self) -> None:
        allowed, wildcard = slc.parse_allow_trailers("fix\n\nAllow-Symbol-Loss: TestA.test_default, func:foo\n")
        self.assertEqual(allowed, {"TestA.test_default", "func:foo"})
        self.assertFalse(wildcard)
        allowed2, wildcard2 = slc.parse_allow_trailers("Allow-Symbol-Loss: *\n")
        self.assertEqual(allowed2, set())
        self.assertTrue(wildcard2)

    def test_waives_matches_full_key_and_stripped_name(self) -> None:
        self.assertTrue(slc._waives("method:TestA.test_default", {"TestA.test_default"}))
        self.assertTrue(slc._waives("func:foo", {"func:foo"}))
        self.assertFalse(slc._waives("method:TestB.test_default", {"TestA.test_default"}))


if __name__ == "__main__":
    unittest.main()
