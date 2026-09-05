#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Pin ``util/ad-hoc/2026-08-31_resident_gap_triage.py`` -- the third P5 hazard
tool (gap-scan finding + triage severity).

Failure class this pins
-----------------------
A census that can bury a known-real hazard and still print success.

The first version scored a 2-sentence sliding window. The owner-settled
cascor ``max_epochs`` / ``output_epochs`` split (finding L-2) scored **2**
and was buried, because the prohibition and the silence marker sit four
paragraphs apart. Window scoring is the same vacuous-pass class as a
per-line scorer that found 0 of 4 real hazards in this repo's own
``AGENTS.md``, and as an X7 census that certified 36 sites where 58 is
true.

``#1663`` / ``tests/test_hazard_triage.py`` pins the AGENTS.md finder.
This suite pins the leftover that finder cannot see: scoring SOURCE
comments that are resident nowhere, with a demotion that must never
drop a remaining-score hit.

Hermetic: TemporaryDirectory repos only. ``gh api`` is never called.
``util/`` is outside every pre-commit Python hook, so this suite is the gate.
"""

from __future__ import annotations

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-31_resident_gap_triage.py"

# Spread signals the way the documented L-2 miss does: prohibition, silence,
# and irreversibility in sentences no 2-sentence window can pair.
_SPREAD = "Do not set output_epochs_alias to be thorough. " "Filler sentence one about ordinary configuration and nothing else here. " "Filler sentence two about ordinary configuration and nothing else here. " "That choice silently diverges the service from the CLI path. " "Filler sentence three about ordinary configuration and nothing else here. " "This destroys the live importer and cannot be undone."
_SPREAD_COMMENT = "# " + _SPREAD + "\n"


def _load():
    spec = importlib.util.spec_from_file_location("resident_gap_triage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _write_repo(root: Path, agents: str | None, files: dict[str, str]) -> Path:
    if agents is not None:
        (root / "AGENTS.md").write_text(agents, encoding="utf-8")
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _comment(text: str) -> str:
    return "# " + text + "\n"


class ScoreWindowTest(unittest.TestCase):
    def test_block_score_beats_every_two_sentence_window(self):
        """The documented first-version miss: spread signals, window score < block score."""
        block_n, hits, demoted = mod.score_window(_SPREAD)
        self.assertGreaterEqual(block_n, 3, f"fixture no longer carries 3 signals: {hits}")
        self.assertIn("prohibition", hits)
        self.assertIn("silent-failure", hits)
        self.assertIn("irreversible", hits)
        self.assertEqual(demoted, [])
        window_scores = [mod.score_window(w)[0] for w in mod.windows(_SPREAD)]
        self.assertTrue(window_scores, "windows() returned no windows for the spread fixture")
        self.assertLess(
            max(window_scores),
            block_n,
            f"a 2-sentence window already equals the block ({max(window_scores)} vs {block_n}); " "fixture is not the documented miss",
        )

    def test_log_level_warning_demotes_hazard_noun_only(self):
        win = "logger.warning is the default WARNING level for the log shipper and nothing else of note."
        n, hits, demoted = mod.score_window(win)
        self.assertEqual(n, 0)
        self.assertEqual(hits, [])
        self.assertEqual(demoted, ["hazard-noun: level name in a logging context"])

    def test_footgun_keeps_hazard_noun_in_a_logging_sentence(self):
        """OTHER_NOUNS (footgun) blocks the demotion. A real hazard that happens to mention WARNING stays."""
        win = "logger.warning is a footgun WARNING at the log shipper default."
        n, hits, demoted = mod.score_window(win)
        self.assertEqual(n, 1)
        self.assertEqual(hits, ["hazard-noun"])
        self.assertEqual(demoted, [])

    def test_demotion_never_drops_a_remaining_score(self):
        """FALSE POSITIVES ARE DEMOTED, NEVER DROPPED -- remaining prohibition still scores."""
        win = "Do not log this unique_hazard_token. " "logger.warning at WARNING level goes to the log shipper for operators."
        n, hits, demoted = mod.score_window(win)
        self.assertEqual(n, 1)
        self.assertEqual(hits, ["prohibition"])
        self.assertEqual(demoted, ["hazard-noun: level name in a logging context"])


class WindowsTest(unittest.TestCase):
    def test_windows_emits_singletons_and_pairs(self):
        text = "Alpha one. Beta two. Gamma three."
        self.assertEqual(
            mod.windows(text),
            [
                "Alpha one.",
                "Beta two.",
                "Gamma three.",
                "Alpha one. Beta two.",
                "Beta two. Gamma three.",
            ],
        )

    def test_windows_empty_on_blank(self):
        self.assertEqual(mod.windows(""), [])
        self.assertEqual(mod.windows("   "), [])


class TriageRepoTest(unittest.TestCase):
    def test_spread_block_is_a_gap_and_keeps_the_block_score(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={"src/mod.py": _SPREAD_COMMENT},
            )
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(len(rows), 1, rows)
        row = rows[0]
        self.assertEqual(row["file"], "src/mod.py")
        self.assertGreaterEqual(row["score"], 3)
        self.assertIn("prohibition", row["signals"])
        self.assertIn("silent-failure", row["signals"])
        self.assertIn("irreversible", row["signals"])
        self.assertEqual(row["demoted"], [])
        # A window-scoring rewrite would store max(window) == 2.
        self.assertGreater(
            row["score"],
            max(mod.score_window(w)[0] for w in mod.windows(_SPREAD)),
        )

    def test_identifier_already_in_agents_is_not_a_gap(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="resident mention of output_epochs_alias lives here\n",
                files={"src/mod.py": _SPREAD_COMMENT},
            )
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(rows, [], f"gap predicate leaked a resident identifier: {rows}")

    def test_missing_agents_md_returns_empty(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(Path(tmp), agents=None, files={"src/mod.py": _SPREAD_COMMENT})
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(rows, [])

    def test_test_filename_is_skipped(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty\n",
                files={"src/test_hidden.py": _SPREAD_COMMENT},
            )
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(rows, [], f"test_*.py leaked into the census: {rows}")

    def test_worktrees_dir_is_skipped(self):
        """The 2026-08-31 worktree-multiplication class: one result counted once per copy."""
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty\n",
                files={"worktrees/copy/src/mod.py": _SPREAD_COMMENT},
            )
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(rows, [], f"worktrees/ copy leaked into the census: {rows}")

    def test_short_block_is_skipped(self):
        short = "# NEVER silently delete this.\n"
        self.assertLess(len(short.lstrip("# ").strip()), 60)
        with TemporaryDirectory() as tmp:
            root = _write_repo(Path(tmp), agents="# empty\n", files={"src/mod.py": short})
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(rows, [])

    def test_demoted_row_still_printed_when_score_remains(self):
        text = "Do not log this unique_hazard_token. " "logger.warning at WARNING level goes to the log shipper for operators."
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty\n",
                files={"src/mod.py": _comment(text)},
            )
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["score"], 1)
        self.assertEqual(rows[0]["signals"], ["prohibition"])
        self.assertEqual(rows[0]["demoted"], ["hazard-noun: level name in a logging context"])

    def test_silent_failure_sorts_before_a_tied_non_silent_row(self):
        silent = "Do not set beta_token_zzz to be thorough. That choice silently diverges the service."
        other = "Do not set alpha_token_zzz to be thorough. This destroys the live importer immediately."
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty\n",
                files={
                    "src/a_irreversible.py": _comment(other),
                    "src/b_silent.py": _comment(silent),
                },
            )
            rows = mod.triage_repo(root, None, "AGENTS.md", 60)
        self.assertEqual([r["score"] for r in rows], [2, 2], rows)
        self.assertIn("silent-failure", rows[0]["signals"])
        self.assertNotIn("silent-failure", rows[1]["signals"])
        self.assertEqual(rows[0]["file"], "src/b_silent.py")


class MainAndSelfCheckTest(unittest.TestCase):
    def test_min_score_filters_print_not_json(self):
        """--min-score is a print threshold. JSON dumps every scored row so suppressions stay visible."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, agents="# empty\n", files={"src/mod.py": _SPREAD_COMMENT})
            out_json = root / "rows.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.main([str(root), "--min-score", "4", "--json", str(out_json)])
            self.assertEqual(rc, 0)
            printed = buf.getvalue()
            self.assertIn("0 at score >= 4", printed)
            self.assertNotIn("[3] src/mod.py", printed)
            dumped = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(len(dumped), 1)
            self.assertEqual(dumped[0]["score"], 3)

    def test_self_check_fails_when_the_known_line_is_absent(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty\n",
                files={"src/mod.py": _SPREAD_COMMENT},
            )
            rc = mod.self_check(root, "AGENTS.md")
        self.assertEqual(rc, 1)

    def test_self_check_fails_when_agents_md_is_missing(self):
        with TemporaryDirectory() as tmp:
            root = _write_repo(Path(tmp), agents=None, files={"src/mod.py": _SPREAD_COMMENT})
            rc = mod.self_check(root, "AGENTS.md")
        self.assertEqual(rc, 1)

    def test_self_check_passes_the_synthetic_l2_control(self):
        """Positive control without a live cascor tree: line 1927 of cascade_correlation.py."""
        lines = ["x = 1"] * 1926
        lines.extend(_SPREAD_COMMENT.splitlines())
        body = "\n".join(lines) + "\n"
        with TemporaryDirectory() as tmp:
            root = _write_repo(
                Path(tmp),
                agents="# empty resident file\n",
                files={"src/cascade_correlation.py": body},
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.self_check(root, "AGENTS.md")
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertIn("SELF-CHECK PASS", buf.getvalue())
            self.assertIn("cascade_correlation.py:1927", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
