"""Tests for util/sequence_safety/symbol_loss_check.py -- the AST symbol-loss screen.

Hermetic: every case builds a throwaway git repo under a tempdir (``git -C``, never
``cd``) with a BASE commit and a HEAD commit, then drives the CLI as a subprocess and
asserts the verdicts + exit code. Mirrors the fixture style of
``tests/test_worktree_cleanup.py``. No custom subprocess env is needed -- the fixtures
pin ``user.name`` / ``user.email`` / ``commit.gpgsign`` repo-locally and the module only
*reads* git (rev-parse / cat-file / diff / log), so nothing signs; the RedactedEnv house
rule applies only to raw ``os.environ`` mappings, of which there are none here.

Coverage: clean pass, LOST detection (same-file), the SF3 bare-name masking pin (a
deleted ``TestA.test_default`` is NOT hidden by an unrelated ``TestB.test_default``),
qualified-name relocation (a genuine move is WARN not FAIL), the WEAKENED threshold arms
(shrink past 0.6 + >=4 delta FAILs; a small shrink and a same-length gutting do NOT),
DUPLICATED, import/const-removal advisory WARN, bash LOST-FAIL / WEAKENED-WARN, the
``Allow-Symbol-Loss`` trailer escape + wildcard rejection, and exit codes 0/1/2.

util/ is not a package; the module is importlib-loaded for direct helper unit tests.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TIMEOUT = 30


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_SCRIPT = _REPO_ROOT / "util" / "sequence_safety" / "symbol_loss_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("symbol_loss_check", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the module's @dataclass annotations (stringized by
    # ``from __future__ import annotations``) resolve via sys.modules[spec.name].
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_SLC = _load()


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
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


def _run_cli(root: Path, *extra: str, base: str = "HEAD~1", head: str = "HEAD") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--base", base, "--head", head, "--repo-root", str(root), *extra],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )


def _report(cp: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(cp.stdout)


def _by_symbol(report: dict) -> dict:
    return {f["symbol"]: f for f in report["findings"]}


class SymbolLossBehaviourTest(unittest.TestCase):
    """End-to-end verdicts against real git fixture repos."""

    def test_additions_only_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n\n    def b(self):\n        return 2\n")
            _commit(root, "add method b")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_report(cp)["stats"]["fail_count"], 0)

    def test_same_file_method_deletion_is_lost_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n\n    def drop_me(self):\n        return 2\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n")
            _commit(root, "drop drop_me")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("method:TestX.drop_me")
            self.assertIsNotNone(f, msg=cp.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("LOST", "FAIL"))

    def test_bare_name_collision_does_not_mask_a_real_deletion(self) -> None:
        """SF3 pin: deleting TestA.test_default while an unrelated TestB.test_default
        exists must still FAIL on the qualified key -- never masked by the bare name."""
        with tempfile.TemporaryDirectory() as tmp:
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
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            by = _by_symbol(_report(cp))
            self.assertIn("method:TestA.test_default", by)
            self.assertEqual(by["method:TestA.test_default"]["severity"], "FAIL")
            # TestB.test_default is untouched -> it must not appear as any finding.
            self.assertNotIn("method:TestB.test_default", by)

    def test_qualified_relocation_is_warn_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
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
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("method:TestA.moved")
            self.assertIsNotNone(f, msg=cp.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("RELOCATED", "WARN"))
            self.assertEqual(f["detail"]["match"], "qualified-name")

    def test_weakened_shrink_past_threshold_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def big():\n    a = 1\n    b = 2\n    c = 3\n    d = 4\n    e = 5\n    return a + b + c + d + e\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def big():\n    return 0\n")
            _commit(root, "gut big")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("func:big")
            self.assertIsNotNone(f, msg=cp.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("WEAKENED", "FAIL"))

    def test_small_shrink_below_threshold_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def f():\n    a = 1\n    b = 2\n    return a + b\n")
            _commit(root, "base")
            # 4 lines -> 3 lines: delta 1 (< 4) and ratio 0.75 (> 0.6) -> not WEAKENED.
            _write(root, "util/h.py", "def f():\n    a = 1\n    return a\n")
            _commit(root, "minor edit")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertNotIn("func:f", _by_symbol(_report(cp)))

    def test_same_length_gutting_is_invisible_blind_spot(self) -> None:
        """Documented WEAKENED blind spot: a same-line-count body swap has delta 0 and
        is not flagged (that class needs mypy / human review, not this screen)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def f():\n    a = compute_real_thing()\n    b = another_real_thing()\n    return a + b\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def f():\n    a = 0\n    b = 0\n    return a + b\n")
            _commit(root, "gut but keep line count")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertNotIn("func:f", _by_symbol(_report(cp)))

    def test_duplicated_definition_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def dup():\n    return 1\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def dup():\n    return 1\n\n\ndef dup():\n    return 2\n")
            _commit(root, "fuse a duplicate dup")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("func:dup")
            self.assertIsNotNone(f, msg=cp.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("DUPLICATED", "FAIL"))

    def test_property_setter_pair_is_not_false_duplicated(self) -> None:
        """Accessor-pair guard (``_accessor_suffix``, backported from the cascor port): a
        ``@property`` getter and its ``@x.setter`` share a method name but are keyed
        distinctly (``method:C.value`` vs ``method:C.value.setter``), so an unchanged
        accessor pair is NEVER a false DUPLICATED -- while a genuine same-name method
        re-definition (no accessor decorator) in the same file still DUPLICATEs. Without
        the suffix both accessors collapse onto ``method:C.value`` (count 2) and the pair
        false-FAILs on every PR touching such a file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            base = "class C:\n" "    @property\n" "    def value(self):\n" "        return self._v\n\n" "    @value.setter\n" "    def value(self, v):\n" "        self._v = v\n\n" "    def plain(self):\n" "        return 1\n"
            _write(root, "util/acc.py", base)
            _commit(root, "base")
            # head: keep the accessor pair verbatim (must NOT DUPLICATE) but genuinely
            # re-define `plain` (a real same-name method dup that MUST still FAIL).
            head = base + "\n    def plain(self):\n        return 2\n"
            _write(root, "util/acc.py", head)
            _commit(root, "redefine plain (real dup), keep the property/setter pair")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            by = _by_symbol(_report(cp))
            # the getter + setter each stay count 1 under distinct keys -> no finding.
            self.assertNotIn("method:C.value", by, msg=cp.stdout)
            self.assertNotIn("method:C.value.setter", by, msg=cp.stdout)
            # the genuine re-definition of `plain` IS duplicated.
            dup = by.get("method:C.plain")
            self.assertIsNotNone(dup, msg=cp.stdout)
            self.assertEqual((dup["verdict"], dup["severity"]), ("DUPLICATED", "FAIL"))

    def test_removed_import_and_const_are_advisory_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "import os\n\nFOO = 1\n\n\ndef keep():\n    return FOO\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 1\n")
            _commit(root, "drop import + const")
            cp = _run_cli(root, "--json")
            # import/const removal is advisory WARN only -> no FAIL, exit 0.
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            by = _by_symbol(_report(cp))
            self.assertEqual(by["import:os"]["severity"], "WARN")
            self.assertEqual(by["const:FOO"]["severity"], "WARN")

    def test_bash_function_deletion_is_lost_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo foo\n}\n\nbar() {\n    echo bar\n}\n")
            _commit(root, "base")
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo foo\n}\n")
            _commit(root, "drop bar")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("fn:bar")
            self.assertIsNotNone(f, msg=cp.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("LOST", "FAIL"))

    def test_bash_weakened_is_warn_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo 1\n    echo 2\n    echo 3\n    echo 4\n    echo 5\n    echo 6\n}\n")
            _commit(root, "base")
            _write(root, "util/s.bash", "#!/usr/bin/env bash\nfoo() {\n    echo 1\n}\n")
            _commit(root, "gut foo")
            cp = _run_cli(root, "--json")
            # bash regex is crude, so a shrink is WARN-only (advisory) -> exit 0.
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("fn:foo")
            if f is not None:
                self.assertEqual(f["severity"], "WARN")

    def test_deleted_file_flags_every_definition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_gone.py", "class TestGone:\n    def a(self):\n        return 1\n\n    def b(self):\n        return 2\n")
            _write(root, "tests/test_stay.py", "class TestStay:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            (root / "tests" / "test_gone.py").unlink()
            _commit(root, "delete whole test file")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            by = _by_symbol(_report(cp))
            self.assertEqual(by["method:TestGone.a"]["verdict"], "LOST")
            self.assertEqual(by["method:TestGone.b"]["verdict"], "LOST")


class SymbolLossEscapeHatchTest(unittest.TestCase):
    """The Allow-Symbol-Loss commit-trailer escape + wildcard rejection."""

    def test_trailer_waives_enumerated_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef stays():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def stays():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: gone")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            f = _by_symbol(_report(cp)).get("func:gone")
            self.assertIsNotNone(f, msg=cp.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("WAIVED", "WAIVED"))

    def test_trailer_accepts_kind_qualified_form(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: func:gone")
            cp = _run_cli(root, "--json")
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertEqual(_by_symbol(_report(cp))["func:gone"]["severity"], "WAIVED")

    def test_wildcard_trailer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone\n\nAllow-Symbol-Loss: *")
            cp = _run_cli(root, "--json")
            # A blanket wildcard waives nothing -> the deletion still FAILs.
            self.assertEqual(cp.returncode, 1, msg=cp.stderr)
            report = _report(cp)
            self.assertTrue(report["stats"]["wildcard_rejected"])
            self.assertEqual(_by_symbol(report)["func:gone"]["severity"], "FAIL")


class SymbolLossCliContractTest(unittest.TestCase):
    """Exit-code + argument contract."""

    def test_missing_base_is_usage_error(self) -> None:
        cp = subprocess.run([sys.executable, str(_SCRIPT), "--head", "HEAD"], capture_output=True, text=True, timeout=_TIMEOUT)
        self.assertEqual(cp.returncode, 2)

    def test_unresolvable_ref_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            cp = _run_cli(root, base="does-not-exist", head="HEAD")
            self.assertEqual(cp.returncode, 2)
            self.assertIn("could not resolve ref", cp.stderr)

    def test_explicit_files_bypasses_scope_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            # scripts/ is out of the default scope; --files targets it directly.
            _write(root, "scripts/tool.py", "def helper():\n    return 1\n")
            _commit(root, "base")
            _write(root, "scripts/tool.py", "x = 1\n")
            _commit(root, "drop helper")
            auto = _run_cli(root, "--json")
            self.assertEqual(auto.returncode, 0, msg=auto.stderr)  # scripts/ excluded by default
            explicit = _run_cli(root, "--files", "scripts/tool.py", "--json")
            self.assertEqual(explicit.returncode, 1, msg=explicit.stderr)
            self.assertEqual(_by_symbol(_report(explicit))["func:helper"]["verdict"], "LOST")


class SymbolLossAdvisoryTest(unittest.TestCase):
    """The --advisory (per-PR allow-symbol-loss label hatch) exit-0 downgrade."""

    def test_advisory_downgrades_fail_to_exit_0_but_keeps_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n\n    def drop_me(self):\n        return 2\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def keep(self):\n        return 1\n")
            _commit(root, "drop drop_me")
            # Strict (no flag): the silent deletion FAILs -> exit 1 (normal FAIL unchanged).
            strict = _run_cli(root, "--json")
            self.assertEqual(strict.returncode, 1, msg=strict.stderr)
            # --advisory: exit 0, but the FAIL finding is left intact in the report (ground
            # truth preserved for the sequence-safety-report artifact) and advisory is recorded.
            adv = _run_cli(root, "--advisory", "--json")
            self.assertEqual(adv.returncode, 0, msg=adv.stderr)
            report = _report(adv)
            self.assertTrue(report["advisory"])
            f = _by_symbol(report).get("method:TestX.drop_me")
            self.assertIsNotNone(f, msg=adv.stdout)
            self.assertEqual((f["verdict"], f["severity"]), ("LOST", "FAIL"))
            self.assertEqual(report["stats"]["fail_count"], 1)

    def test_advisory_human_output_prints_downgrade_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "util/h.py", "def gone():\n    return 1\n\n\ndef keep():\n    return 2\n")
            _commit(root, "base")
            _write(root, "util/h.py", "def keep():\n    return 2\n")
            _commit(root, "drop gone")
            adv = _run_cli(root, "--advisory")  # human (non-json) output
            self.assertEqual(adv.returncode, 0, msg=adv.stderr)
            self.assertIn("ADVISORY", adv.stdout)

    def test_advisory_clean_diff_is_still_exit_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n\n    def b(self):\n        return 2\n")
            _commit(root, "add method b")
            adv = _run_cli(root, "--advisory", "--json")
            self.assertEqual(adv.returncode, 0, msg=adv.stderr)
            report = _report(adv)
            self.assertTrue(report["advisory"])
            self.assertEqual(report["stats"]["fail_count"], 0)

    def test_advisory_does_not_mask_invocation_error_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write(root, "tests/test_x.py", "class TestX:\n    def a(self):\n        return 1\n")
            _commit(root, "base")
            # An unresolvable ref is an invocation error -> exit 2 even under --advisory.
            adv = _run_cli(root, "--advisory", base="does-not-exist", head="HEAD")
            self.assertEqual(adv.returncode, 2, msg=adv.stdout)


class SymbolLossHelperUnitTest(unittest.TestCase):
    """Direct unit tests for the pure helpers (importlib-loaded module)."""

    def test_in_scope(self) -> None:
        self.assertTrue(_SLC.in_scope("tests/test_x.py"))
        self.assertTrue(_SLC.in_scope("util/a/b.py"))
        self.assertTrue(_SLC.in_scope("util/s.bash"))
        self.assertFalse(_SLC.in_scope("tests/sub/test_x.py"))  # nested tests/ subdir
        self.assertFalse(_SLC.in_scope("scripts/x.py"))
        self.assertFalse(_SLC.in_scope("juniper-ci-tools/src/x.py"))
        self.assertFalse(_SLC.in_scope("docs/x.md"))

    def test_py_symbols_qualifies_methods(self) -> None:
        syms = _SLC.py_symbols("class A:\n    def m(self):\n        return 1\n\n\ndef f():\n    return 2\n")
        self.assertIn("class:A", syms)
        self.assertIn("method:A.m", syms)
        self.assertIn("func:f", syms)

    def test_py_symbols_returns_none_on_syntax_error(self) -> None:
        self.assertIsNone(_SLC.py_symbols("def broken(:\n"))

    def test_parse_allow_trailers_enumerates_and_flags_wildcard(self) -> None:
        allowed, wildcard = _SLC.parse_allow_trailers("fix\n\nAllow-Symbol-Loss: TestA.test_default, func:foo\n")
        self.assertEqual(allowed, {"TestA.test_default", "func:foo"})
        self.assertFalse(wildcard)
        allowed2, wildcard2 = _SLC.parse_allow_trailers("Allow-Symbol-Loss: *\n")
        self.assertEqual(allowed2, set())
        self.assertTrue(wildcard2)

    def test_waives_matches_full_key_and_stripped_name(self) -> None:
        self.assertTrue(_SLC._waives("method:TestA.test_default", {"TestA.test_default"}))
        self.assertTrue(_SLC._waives("func:foo", {"func:foo"}))
        self.assertFalse(_SLC._waives("method:TestB.test_default", {"TestA.test_default"}))


if __name__ == "__main__":
    unittest.main()
