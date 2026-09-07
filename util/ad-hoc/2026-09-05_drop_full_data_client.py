#!/usr/bin/env python3
"""Decision 11, consumer side: take the ``*_full`` family out of juniper-data-client.

Project:     Juniper
Sub-Project: juniper-data-client
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data-client#190

Consumers first, producer second. Design §9.5's backward-compatibility clause is
explicit: every stored artifact still carries ``X_full``, so consumers must keep
TOLERATING it -- only the REQUIREMENT is dropped. Relaxing the consumers while the
producer still emits is safe in both directions; doing it the other way round breaks
every reader the moment the producer stops.

Three sites here, and the third is a product decision the design flagged:

* ``fake_client``'s ``n_full`` was ``len(X_full)``. It becomes the partition sum,
  which is what ``DatasetMeta.n_samples`` has been since juniper-data#358 -- so the
  fake now agrees with the real service rather than measuring an array the service no
  longer emits.
* ``get_preview`` served the first *n* rows of ``X_full``. §9.5.4 item 3 names ``train``
  as the replacement and says the semantics shift slightly. They do, and not uniformly:
  for a shuffled tabular artifact train is distributionally the same as the whole set,
  but for a SEQUENCE artifact train is the chronologically earliest block, so a preview
  is no longer a sample of the later rows. That is written into the docstring rather
  than left for a caller to discover.
"""

from __future__ import annotations

import pathlib
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data-client--feature--drop-full-family--20260905-1215--7d5b2f60")

META_OLD = '''        n_train = arrays["X_train"].shape[0]
        n_val = arrays["X_val"].shape[0]
        n_test = arrays["X_test"].shape[0]
        n_full = arrays["X_full"].shape[0]
'''
META_NEW = '''        n_train = arrays["X_train"].shape[0]
        n_val = arrays["X_val"].shape[0]
        n_test = arrays["X_test"].shape[0]
        # The partition SUM, not len(X_full). Decision 11 removed X_full from the
        # contract, and DatasetMeta.n_samples has been the three-way sum since
        # juniper-data#358 -- so this now agrees with the real service instead of
        # measuring an array the service no longer emits.
        n_full = n_train + n_val + n_test
'''

DOC_OLD = "        Returns the first ``n`` samples from the full dataset (X_full / y_full).\n"
DOC_NEW = '''        Returns the first ``n`` samples of the TRAINING partition.

        It read ``X_full`` until decision 11 removed that key from the contract.
        Serving ``train`` is design section 9.5.4 item 3's stated choice, and it does
        change the semantics slightly: a preview is now a sample of what the model is
        fit on, not of the whole dataset. For a shuffled tabular artifact the two are
        distributionally the same; for a SEQUENCE artifact they are not, because train
        is the chronologically earliest block. A caller wanting later rows should ask
        for the partition it means.
'''

BODY_OLD = '''        arrays = self._datasets[dataset_id]["arrays"]
        X_full = arrays["X_full"]
        y_full = arrays["y_full"]

        # Cap at available samples and the requested count
        n_available = min(n, X_full.shape[0], MAX_PREVIEW_N)

        return {
            "n_samples": int(n_available),
            "X_sample": X_full[:n_available].tolist(),
            "y_sample": y_full[:n_available].tolist(),
        }
'''
BODY_NEW = '''        arrays = self._datasets[dataset_id]["arrays"]
        X_preview = arrays["X_train"]
        y_preview = arrays["y_train"]

        # Cap at available samples and the requested count
        n_available = min(n, X_preview.shape[0], MAX_PREVIEW_N)

        return {
            "n_samples": int(n_available),
            "X_sample": X_preview[:n_available].tolist(),
            "y_sample": y_preview[:n_available].tolist(),
        }
'''

CLIENT_DOC_OLD = "        - X_full, y_full: Full dataset features and one-hot labels\n"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        print(f"REFUSING: {label} matched {text.count(old)}x", file=sys.stderr)
        raise SystemExit(1)
    return text.replace(old, new)


def main() -> int:
    fake = WT / "juniper_data_client/testing/fake_client.py"
    src = fake.read_text()
    src = replace_once(src, META_OLD, META_NEW, "n_full")
    src = replace_once(src, DOC_OLD, DOC_NEW, "preview docstring")
    src = replace_once(src, BODY_OLD, BODY_NEW, "preview body")
    fake.write_text(src)

    client = WT / "juniper_data_client/client.py"
    src = client.read_text()
    if src.count(CLIENT_DOC_OLD) == 1:
        client.write_text(src.replace(CLIENT_DOC_OLD, ""))
        print("client.py: dropped the X_full line from the artifact-key docstring")
    else:
        print(f"client.py: docstring line matched {src.count(CLIENT_DOC_OLD)}x -- left alone", file=sys.stderr)

    print("fake_client.py updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
