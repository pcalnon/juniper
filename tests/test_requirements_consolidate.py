"""Gate for ``util/requirements_consolidate.py`` — the rebuilt v5 consolidation script.

The load-bearing property is round-trip fidelity. The corpus is 1,814 entries spread across
30 rendered markdown files, and 910 of them carry a ``**Detail**:`` section that exists in no
other artifact — the ID ledger has no ``detail`` field at all. A renderer that drops one
optional section deletes that content everywhere at once, in a diff far too large to review.

Three optional elements were found ONLY because the round-trip check failed on them:
a ``**Design**:`` section, a ``*Merged from N extraction candidates (slices: X).*``
provenance line whose ``slices`` value is stored nowhere else, and stray file-level headings
in ``by-area/DATA.md`` and ``by-status/designed.md``. That is why entries re-emit their body
verbatim instead of being re-serialised field by field, and why this suite asserts equality
against the shipped tree rather than against a fixture.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "requirements_consolidate.py"

spec = importlib.util.spec_from_file_location("requirements_consolidate", SCRIPT)
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

FAMILIES = (
    ("by-area", "category", rc.render_area),
    ("by-repo", "owner", rc.render_repo),
    ("by-status", "status", rc.render_status),
)


class RoundTripTest(unittest.TestCase):
    """render(parse(file)) == file, byte for byte, for every shipped view."""

    def test_every_view_file_round_trips(self) -> None:
        checked = 0
        for sub, _attr, renderer in FAMILIES:
            for path in sorted((rc.REQ_ROOT / sub).glob("*.md")):
                text = path.read_text(encoding="utf-8")
                entries = [rc.parse_entry(b) for b in rc._split_blocks(text)]
                with self.subTest(view=f"{sub}/{path.name}"):
                    self.assertEqual(renderer(path.stem, entries, rc._preamble(text)), text)
                checked += 1
        self.assertGreaterEqual(checked, 30, "fewer view files than expected — the contract would pass vacuously")

    def test_the_check_roundtrip_entrypoint_agrees(self) -> None:
        """The CLI gate operators actually run must agree with this suite."""
        self.assertEqual(rc.check_roundtrip(), 0)

    def test_detail_sections_survive_a_round_trip(self) -> None:
        """The specific content at risk: Detail exists only in the views.

        A renderer that silently dropped Detail would still pass a count-based check, so
        this asserts the text itself makes it back.
        """
        entries = rc.load_corpus()
        with_detail = [e for e in entries if e.detail]
        self.assertGreater(len(with_detail), 800, "corpus should carry ~910 Detail sections")
        for entry in with_detail[:50]:
            self.assertIn(entry.detail.split("\n")[0], rc.render_entry(entry))

    def test_view_only_fields_survive_because_the_body_is_verbatim(self) -> None:
        """The merged-provenance line carries a ``slices`` value stored in no other artifact."""
        merged = [e for e in rc.load_corpus() if e.body and "Merged from" in e.body]
        self.assertGreater(len(merged), 0, "corpus should carry merged-provenance lines")
        for entry in merged[:20]:
            self.assertIn("Merged from", rc.render_entry(entry))


class DerivedViewTest(unittest.TestCase):
    """``by-repo`` / ``by-status`` are a PROJECTION of ``by-area``, not independent copies.

    The round-trip contract above proves each file re-renders from its OWN entries — which every
    shipped file satisfied even while the three families disagreed with each other, because
    nothing ever compared them. Measured 2026-08-29 (ml#1415): 52 entries differed between
    by-area and by-repo and 149 between by-area and by-status, on zero id and zero metadata
    differences — trailing punctuation and a blank line after ``**Sources**:``. Independent
    maintenance of three full copies produced that, exactly as the plan's §97 predicted it would.
    These tests are what makes the projection enforceable.
    """

    def test_the_derived_families_match_the_corpus(self) -> None:
        for path, text in rc.render_derived().items():
            with self.subTest(view=f"{path.parent.name}/{path.name}"):
                self.assertTrue(path.is_file(), f"{path} is projected by the corpus but absent")
                self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_the_check_views_entrypoint_agrees(self) -> None:
        """The CLI gate operators actually run must agree with this suite."""
        self.assertEqual(rc.check_views(), 0)

    def test_no_orphan_derived_files(self) -> None:
        """A file the corpus no longer projects — an owner or status that lost its last entry."""
        projected = set(rc.render_derived())
        for sub, _attr, _renderer in rc.DERIVED_FAMILIES:
            for path in sorted((rc.REQ_ROOT / sub).glob("*.md")):
                self.assertIn(path, projected, f"{sub}/{path.name} is on disk but nothing projects into it")

    def test_the_projection_covers_every_entry_exactly_once_per_family(self) -> None:
        """Guards the grouping key, not the rendering: a bad key would silently drop entries."""
        entries = rc.load_corpus()
        rendered = rc.render_derived(entries=entries)
        for sub, _attr, _renderer in rc.DERIVED_FAMILIES:
            ids: "list[str]" = []
            for path, text in rendered.items():
                if path.parent.name == sub:
                    ids += [rc.parse_entry(b).id for b in rc._split_blocks(text)]
            with self.subTest(family=sub):
                self.assertEqual(len(ids), len(entries), f"{sub} projects {len(ids)} of {len(entries)} entries")
                self.assertEqual(len(set(ids)), len(entries), f"{sub} projects a duplicate")

    def test_regeneration_is_idempotent(self) -> None:
        """A second regeneration must change nothing — otherwise the gate would flap in CI."""
        self.assertEqual(rc.regenerate_views(apply=False), [])

    def test_write_all_does_not_touch_the_derived_families(self) -> None:
        """They are owned by the projection; two writers would reintroduce the drift."""
        self.assertEqual([sub for sub, _a, _r in rc.FAMILIES_WRITTEN_BY_WRITE_ALL], ["by-area"])


class CorpusIntegrityTest(unittest.TestCase):
    def test_ids_are_unique(self) -> None:
        ids = [e.id for e in rc.load_corpus()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_view_family_holds_the_whole_corpus(self) -> None:
        """All three families are projections of one corpus; none may be missing an entry."""
        sizes = {}
        for sub, _attr, _renderer in FAMILIES:
            found = set()
            for path in sorted((rc.REQ_ROOT / sub).glob("*.md")):
                found |= {rc.parse_entry(b).id for b in rc._split_blocks(path.read_text(encoding="utf-8"))}
            sizes[sub] = found
        self.assertEqual(sizes["by-area"], sizes["by-repo"])
        self.assertEqual(sizes["by-area"], sizes["by-status"])

    def test_categories_and_owners_are_enumerated(self) -> None:
        """A view file for an unknown code would render with a KeyError at the worst moment."""
        for entry in rc.load_corpus():
            self.assertIn(entry.category, rc.AREA_SCOPES, entry.id)
            self.assertIn(entry.owner, rc.OWNER_REPOS, entry.id)
            self.assertIn(entry.status, rc.STATUSES, entry.id)
            self.assertIn(entry.priority, rc.PRIORITIES, entry.id)

    def test_the_rec_block_is_present_and_official(self) -> None:
        """v5 ratified Q-12: JR-REC-* must be in the corpus, not just in a proposal."""
        rec = [e for e in rc.load_corpus() if e.owner == "rec"]
        self.assertEqual(len(rec), 11)
        self.assertEqual({e.id for e in rec} & {"JR-REC-TRAIN-001", "JR-REC-DEP-001"}, {"JR-REC-TRAIN-001", "JR-REC-DEP-001"})


class MergeTest(unittest.TestCase):
    def _entry(self, brief: str, id: str = "", category: str = "TOOL"):
        """Build a minimal Entry (return type omitted: ``rc`` is loaded dynamically)."""
        return rc.Entry(id=id, owner="rec", category=category, status="proposed", priority="P2", brief=brief)

    def test_an_exact_duplicate_brief_is_folded_not_minted(self) -> None:
        """IDs are permanent and never reused, so a wrong mint cannot be retracted."""
        corpus = [self._entry("Add a widget", id="JR-REC-TOOL-900")]
        merged, report = rc.merge(corpus, [self._entry("add a widget.")])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].merged_count, 2)
        self.assertTrue(any("DEDUP exact" in line for line in report))

    def test_a_near_duplicate_is_folded_by_the_v3_1_overlap_rule(self) -> None:
        corpus = [self._entry("Route per-dataset JSON into a per-run results directory", id="JR-REC-TOOL-901")]
        merged, _ = rc.merge(corpus, [self._entry("Route per-dataset JSON into a per-run results dir")])
        self.assertEqual(len(merged), 1)

    def test_an_unrelated_brief_mints_a_new_id(self) -> None:
        corpus = [self._entry("Add a widget", id="JR-REC-TOOL-001")]
        merged, _ = rc.merge(corpus, [self._entry("Publish the sequence-safety screens to PyPI")])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[1].id, "JR-REC-TOOL-002")

    def test_dedup_does_not_reach_across_buckets(self) -> None:
        """Same words, different category, is a different requirement -- not a duplicate."""
        corpus = [self._entry("Add a widget", id="JR-REC-TOOL-001", category="TOOL")]
        merged, _ = rc.merge(corpus, [self._entry("Add a widget", category="TEST")])
        self.assertEqual(len(merged), 2)

    def test_a_reused_id_is_refused(self) -> None:
        corpus = [self._entry("Add a widget", id="JR-REC-TOOL-001")]
        with self.assertRaises(ValueError):
            rc.merge(corpus, [self._entry("Something entirely different", id="JR-REC-TOOL-001")])


class ExtractionValidationTest(unittest.TestCase):
    """``load_incoming`` refuses malformed input rather than corrupting the corpus with it."""

    def _write(self, tmp: str, body: str) -> Path:
        path = Path(tmp) / "in.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_the_shipped_rec_extraction_validates(self) -> None:
        entries = rc.load_incoming(rc.REQ_ROOT / "v5_rec_extraction.yaml")
        self.assertEqual(len(entries), 11)
        self.assertTrue(all(e.owner == "rec" for e in entries))
        self.assertTrue(all(e.sources for e in entries), "every entry must cite a source")
        self.assertTrue(all(e.detail for e in entries), "every entry must carry a detail")

    def test_an_unknown_category_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "- {id: X, owner: rec, category: NOPE, status: shipped, priority: P0, brief: b}\n")
            with self.assertRaises(ValueError):
                rc.load_incoming(path)

    def test_an_unknown_owner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "- {id: X, owner: zzz, category: TOOL, status: shipped, priority: P0, brief: b}\n")
            with self.assertRaises(ValueError):
                rc.load_incoming(path)

    def test_a_missing_required_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "- {id: X, owner: rec, category: TOOL, status: shipped, priority: P0}\n")
            with self.assertRaises(ValueError):
                rc.load_incoming(path)


if __name__ == "__main__":
    unittest.main()
