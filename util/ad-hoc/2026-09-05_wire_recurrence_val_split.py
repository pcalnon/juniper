#!/usr/bin/env python3
"""Chunk 9: teach the experiment harness the third partition.

Project:     Juniper
Sub-Project: juniper-ml
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 9)

Two edits to ``util/experiments/run_experiment.py``:

* ``RECURRENCE_SPLITS`` gains ``val``. Before it, a recurrence run could select only
  train / test / full, so a caller wanting an in-loop split had to point at ``test``
  and then report a number selected on the split it had trained against -- the same
  defect the arc removes everywhere else. ``validation`` stays REJECTED: the artifact
  key is ``X_val`` and the config value that selects it has to match.

* A ``validation_warnings`` entry when the run is launched with cascor's
  ``JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT`` override set. That override is the
  only way past cascor's section 6.1 refusal, and a run that uses it is reporting a
  metric that early stopping selected on. Section 6.1 rule 2 requires such a run to be
  MARKED, and ``validation_warnings`` is the channel the design names -- already
  honoured by ``make_baseline.py``, which refuses to bless a warned run without
  ``--accept-warnings``. So the warning has teeth rather than being a log line.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/binary-swimming-emerson")
TARGET = BASE / "util/experiments/run_experiment.py"

SPLITS_OLD = 'RECURRENCE_SPLITS = frozenset({"train", "test", "full"})\n'
SPLITS_NEW = '''# The NPZ partition names, which are what ``dataset.split`` and
# ``predict.from_dataset_split`` select. ``val`` was added 2026-09-05 with the third
# partition (juniper-data 0.13.0). Before it a recurrence run could read only train,
# test or full, so a caller wanting an in-loop split had to point at ``test`` -- and
# then report a number selected on the split it trained against.
#
# ``val``, not ``validation``: the artifact key is ``X_val`` and the config value that
# selects it has to match. ``validation`` stays REJECTED, and the two tests pinning
# that rejection are deliberate, not stale.
RECURRENCE_SPLITS = frozenset({"train", "val", "test", "full"})
'''

WARN_ANCHOR = '''        config.setdefault("validation_warnings", []).append(note)
        log.warning("config: %s", note)


class ConfigError(Exception):
'''

WARN_NEW = '''        config.setdefault("validation_warnings", []).append(note)
        log.warning("config: %s", note)


#: cascor's only documented way past its section 6.1 refusal. Spelled out rather than
#: imported: juniper-ml does not depend on juniper-cascor, and a wrong guess here would
#: fail OPEN (no warning recorded) rather than loudly, so the name is pinned by a test.
CASCOR_ALLOW_MISSING_VALIDATION_SPLIT_ENV = "JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT"

#: Values that mean "on" for that override, matching pydantic-settings' bool parsing.
_TRUTHY = frozenset({"1", "true", "t", "yes", "y", "on"})


def _warn_on_missing_validation_split_override(config: dict, env: Optional[Mapping[str, str]] = None) -> None:
    """Record a ``validation_warnings`` entry when the run may report a selected-on metric.

    cascor refuses an artifact without ``X_val`` (design section 6.1 rule 1) precisely so
    that the in-loop signal and the reported score cannot be the same rows.
    ``JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT`` is the override that lets a run
    proceed anyway -- at which point early stopping reads ``X_test`` and the reported
    f1 / roc_auc are no longer held out.

    Section 6.1 rule 2 says such a run must be MARKED, not merely permitted. This is the
    marking: ``validation_warnings`` travels onto the manifest, and ``make_baseline.py``
    already refuses to bless a warned run without ``--accept-warnings``. Warning rather
    than raising is deliberate -- the override exists for a reason (a legacy artifact, a
    producer not yet released) and the harness is not the right place to overrule it.
    """
    source = os.environ if env is None else env
    raw = source.get(CASCOR_ALLOW_MISSING_VALIDATION_SPLIT_ENV)
    if raw is None or str(raw).strip().lower() not in _TRUTHY:
        return
    note = (
        f"{CASCOR_ALLOW_MISSING_VALIDATION_SPLIT_ENV}={raw!r} is set: cascor will accept an artifact with no "
        "X_val and early-stop on X_test instead, so this run's reported f1 / roc_auc are SELECTED-ON rather "
        "than held out. They are not comparable with a run made against a three-way artifact. Unset the "
        "override, or use a juniper-data >= 0.13.0 dataset, to get a held-out score (design section 6.1 rule 2)."
    )
    config.setdefault("validation_warnings", []).append(note)
    log.warning("config: %s", note)


class ConfigError(Exception):
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        print(f"REFUSING: {label} matched {text.count(old)}x", file=sys.stderr)
        raise SystemExit(1)
    return text.replace(old, new)


IMPORT_OLD = "from typing import Any, Dict, List, Optional, Tuple\n"
IMPORT_NEW = "from typing import Any, Dict, List, Mapping, Optional, Tuple\n"


def main() -> int:
    src = TARGET.read_text()
    src = replace_once(src, IMPORT_OLD, IMPORT_NEW, "typing import")
    src = replace_once(src, SPLITS_OLD, SPLITS_NEW, "RECURRENCE_SPLITS")
    src = replace_once(src, WARN_ANCHOR, WARN_NEW, "validation-warning recorder")
    TARGET.write_text(src)
    print("run_experiment.py updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
