#!/usr/bin/env python3
"""Decision 11, producer side: juniper-data stops emitting the ``*_full`` family.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data#369

The production surface is small and centralised -- six emit sites for sixteen
generators -- because the tabular tier all funnels through ``partition_and_assemble``
and the sequence tier through the two windowers. The 400-odd remaining references are
tests and docs.

Two of the six are NOT generators and are deliberately left alone:
``storage/hf_store.py`` and ``storage/kaggle_store.py`` build an artifact from an
EXTERNAL dataset that arrives whole and unpartitioned. Those stores are the one place
where "the whole set" is the input rather than a derived view, and stripping the key
there would mean re-deriving it from partitions the store itself just cut. They are
listed here so the omission is a decision rather than an oversight.

``api/routes/datasets.py``'s preview is a CONSUMER: it read ``X_full`` with a
``train + test`` fallback -- which was R-5 surviving in the preview path, silently
skipping the validation rows. It now serves ``train``, matching design §9.5.4 item 3
and the data-client fake, so the fake and the service cannot disagree.
"""

from __future__ import annotations

import pathlib
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--drop-full-family--20260905-1330--cc15640c")

SEQ_OLD = '''        out[f"{key}_train"] = full[:train_end]
        out[f"{key}_val"] = full[train_end:val_end]
        out[f"{key}_test"] = full[val_end:]
        out[f"{key}_full"] = full
    return out
'''
SEQ_NEW = '''        out[f"{key}_train"] = full[:train_end]
        out[f"{key}_val"] = full[train_end:val_end]
        out[f"{key}_test"] = full[val_end:]
    return out
'''

EQ_SEQ_OLD = '''        for key in _WINDOW_KEYS:
            blocks: list[np.ndarray] = []
            for out in per_ticker:
                for split in splits:
                    blocks.append(out[split][key])
            arrays[f"{key}_full"] = np.concatenate(blocks, axis=0)
        return arrays
'''
EQ_SEQ_NEW = '''        return arrays
'''

PREVIEW_OLD = '''        if "X_full" in data and "y_full" in data:
            X = data["X_full"]
            y = data["y_full"]
        else:
            X = np.vstack([data["X_train"], data["X_test"]])
            y = np.vstack([data["y_train"], data["y_test"]])
'''
PREVIEW_NEW = '''        # The TRAINING partition, per design §9.5.4 item 3. This read ``X_full`` with a
        # ``train + test`` fallback -- which was risk R-5 surviving in the preview path,
        # silently skipping the validation rows whenever the artifact had them.
        #
        # Serving train rather than a reassembled whole is the design's stated choice and
        # matches juniper-data-client's fake, so the two cannot disagree. It does shift the
        # semantics for a SEQUENCE artifact, where train is the chronologically earliest
        # block rather than a random sample.
        X = data["X_train"]
        y = data["y_train"]
'''


def replace_once(path: pathlib.Path, old: str, new: str, expected: int, label: str) -> None:
    src = path.read_text()
    found = src.count(old)
    if found != expected:
        print(f"REFUSING: {label} matched {found}x, expected {expected}", file=sys.stderr)
        raise SystemExit(1)
    path.write_text(src.replace(old, new))
    print(f"{label}: {expected} site(s) updated")


def main() -> int:
    replace_once(WT / "juniper_data/generators/_sequence.py", SEQ_OLD, SEQ_NEW, 2, "_sequence.py windowers")
    replace_once(WT / "juniper_data/generators/equities_seq/generator.py", EQ_SEQ_OLD, EQ_SEQ_NEW, 1, "equities_seq assembly")
    replace_once(WT / "juniper_data/api/routes/datasets.py", PREVIEW_OLD, PREVIEW_NEW, 1, "preview endpoint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
