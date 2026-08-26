#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``release: published`` must remain the ONLY automatic trigger on every publish
workflow -- that trigger IS the release-convention gate.

Two distinct hazards are pinned here, and they pull in opposite directions.

**Re-adding ``push:`` re-creates the #555 race.** Cutting a GitHub Release also
creates the tag, which emits a ``push: tags`` event. A workflow subscribed to
both fires TWO concurrent publish runs that race the *immutable* TestPyPI
upload: one wins, the other 400s with "file already exists" and fails the
release. Every publisher deliberately dropped ``push:`` afterwards.

**Removing ``release:`` disarms publishing entirely** -- silently, because a
workflow that never fires reports nothing at all.

The dead gate this replaced
---------------------------
Each of the six sub-package publishers carried a ``Require a GitHub Release for
this tag`` step gated on ``if: github.event_name == 'push'``. With ``push`` not
in ``on:``, that condition was never true and the step could never run. Dead
code shaped like a guard is worse than no guard: it reads as though a bare
``git push <tag>`` is blocked, so a reader stops looking.

The real property is stronger than that step ever was. With ``release:
published`` as the only automatic trigger, a bare tag push starts NO run --
nothing is built, nothing is uploaded. Verified 2026-08-24: 12 tags exist with
no Release, and none of them published anything.

``workflow_dispatch`` stays: it is the deliberate manual escape hatch, and it
cannot fire by accident.

Run: python3 -m unittest -v tests/test_publish_release_only_trigger.py
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

# Every publish workflow in the repo: the meta-package plus the six shared
# sub-packages. Discovered by glob so a NEW publisher cannot dodge this gate by
# simply not being listed here.
PUBLISH_GLOB = "publish*.yml"

# The dead-gate condition. Any step carrying it is unreachable by construction,
# because no publish workflow subscribes to `push`.
DEAD_GATE_CONDITION = "github.event_name == 'push'"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(doc: dict) -> dict:
    """``on:`` parses as the boolean True under YAML 1.1, so accept both keys."""
    on = doc.get("on")
    if on is None:
        on = doc.get(True)
    return on or {}


def _publish_workflows() -> list[Path]:
    return sorted(WORKFLOW_DIR.glob(PUBLISH_GLOB))


class PublishWorkflowDiscoveryTest(unittest.TestCase):
    """A glob that matches nothing would make every test below vacuously pass."""

    def test_publish_workflows_are_found(self) -> None:
        found = _publish_workflows()
        self.assertGreaterEqual(
            len(found),
            7,
            msg=f"expected the meta-package + 6 sub-package publishers, found {[p.name for p in found]}",
        )


class ReleaseOnlyTriggerTest(unittest.TestCase):
    """``release: published`` in, ``push`` out -- on every publisher."""

    def test_release_published_is_a_trigger(self) -> None:
        for wf in _publish_workflows():
            with self.subTest(workflow=wf.name):
                on = _triggers(_load(wf))
                self.assertIn("release", on, msg=f"{wf.name} would never publish")
                types = (on.get("release") or {}).get("types") or []
                self.assertIn("published", types, msg=f"{wf.name}: release types={types}")

    def test_push_is_not_a_trigger(self) -> None:
        """Re-adding ``push:`` double-fires and races the immutable upload (#555)."""
        for wf in _publish_workflows():
            with self.subTest(workflow=wf.name):
                on = _triggers(_load(wf))
                self.assertNotIn(
                    "push",
                    on,
                    msg=(f"{wf.name} subscribes to push: cutting a Release also creates the tag, so this " "fires TWO concurrent publish runs that race the immutable TestPyPI upload (#555)"),
                )

    def test_no_step_is_gated_on_a_push_event(self) -> None:
        """A step conditioned on a push event is unreachable -- a guard that cannot run."""
        for wf in _publish_workflows():
            with self.subTest(workflow=wf.name):
                doc = _load(wf)
                for job_name, job in (doc.get("jobs") or {}).items():
                    for step in job.get("steps") or []:
                        cond = str(step.get("if") or "")
                        self.assertNotIn(
                            DEAD_GATE_CONDITION,
                            cond,
                            msg=(f"{wf.name}:{job_name} step {step.get('name')!r} is gated on a push event, " "but this workflow does not subscribe to push -- it can never run"),
                        )

    def test_workflow_dispatch_escape_hatch_is_retained(self) -> None:
        for wf in _publish_workflows():
            with self.subTest(workflow=wf.name):
                self.assertIn("workflow_dispatch", _triggers(_load(wf)))


if __name__ == "__main__":
    unittest.main()
