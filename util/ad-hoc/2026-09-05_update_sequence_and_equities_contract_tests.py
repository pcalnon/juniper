#!/usr/bin/env python3
"""Take the sequence + equities NPZ-contract assertions three-way.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3b)

Every one of these is risk **R-5** — ``full == train + test`` — in a different
costume. The identity is correct today and false the moment ``val`` is carved
between the two, so each site has to state the third partition explicitly
rather than be relaxed into a ``>=``.

Three shapes:

* ``_assert_regular_sequence_contract`` — copied verbatim into five regular-Δt
  generator test modules (ar_p, delay_product, irregular_sine, mackey_glass,
  multi_sine). Same two lines in each; the key-presence loop has to learn
  ``val`` too or a missing ``X_val`` would go unnoticed.
* ``test_equities_seq_generator`` — same identity, spelled inline.
* ``test_equities_generator`` — the flat (non-sequence) equities split, plus
  two fixtures whose ``train_ratio`` + ``test_ratio`` summed to exactly 1.0 and
  now over-subscribe against the 0.1 ``val_ratio`` default.

Each identity gains a non-empty ``X_val`` assertion first. Without it the
three-way form still passes when ``val`` silently rounds to zero rows — which
is precisely the failure the arc exists to prevent, and it would read green.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--sequence-val-split--20260905-0228--4b9f4b94/juniper_data/tests/unit")

REGULAR_SEQ_MODULES = [
    "test_ar_p_generator.py",
    "test_delay_product_generator.py",
    "test_irregular_sine_generator.py",
    "test_mackey_glass_generator.py",
    "test_multi_sine_generator.py",
]

SPLIT_LOOP_OLD = '    for split in ("train", "test", "full"):\n'
SPLIT_LOOP_NEW = '    for split in ("train", "val", "test", "full"):\n'

IDENTITY_OLD = (
    '    assert n_windows == arrays["X_train"].shape[0] + arrays["X_test"].shape[0]\n'
    '    np.testing.assert_array_equal(arrays["X_full"], np.concatenate([arrays["X_train"], arrays["X_test"]]))\n'
)
IDENTITY_NEW = (
    '    # full == train + val + test, chronological. The non-empty check comes first\n'
    '    # deliberately: the three-way identity also holds when val rounds to zero rows,\n'
    '    # so without it this assertion would pass on exactly the defect it exists to catch.\n'
    '    assert arrays["X_val"].shape[0] > 0, "val partition must be non-empty"\n'
    '    assert n_windows == arrays["X_train"].shape[0] + arrays["X_val"].shape[0] + arrays["X_test"].shape[0]\n'
    '    np.testing.assert_array_equal(arrays["X_full"], np.concatenate([arrays["X_train"], arrays["X_val"], arrays["X_test"]]))\n'
)

# (filename, old, new, expected occurrences)
EDITS: list[tuple[str, str, str, int]] = [
    # --- equities sequence generator -------------------------------------
    (
        "test_equities_seq_generator.py",
        '        for split in ("train", "test", "full"):\n',
        '        for split in ("train", "val", "test", "full"):\n',
        1,
    ),
    (
        "test_equities_seq_generator.py",
        '    def test_full_equals_train_plus_test(self) -> None:\n'
        '        arrays = _generate(["AAPL"], {"AAPL": _ohlcv(seed=3)}, _shares(), lookback=5)\n'
        '        assert arrays["X_full"].shape[0] == arrays["X_train"].shape[0] + arrays["X_test"].shape[0]\n',
        '    def test_full_equals_train_plus_val_plus_test(self) -> None:\n'
        '        arrays = _generate(["AAPL"], {"AAPL": _ohlcv(seed=3)}, _shares(), lookback=5)\n'
        '        assert arrays["X_val"].shape[0] > 0, "val partition must be non-empty"\n'
        '        assert arrays["X_full"].shape[0] == arrays["X_train"].shape[0] + arrays["X_val"].shape[0] + arrays["X_test"].shape[0]\n',
        1,
    ),
    # --- equities flat generator -----------------------------------------
    (
        "test_equities_generator.py",
        '        for key in ("X_train", "y_train", "X_test", "y_test", "X_full", "y_full", "y_reg_full", "ticker_code_full", "date_full", "ticker_vocab"):\n',
        '        for key in ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full", "y_reg_full", "ticker_code_full", "date_full", "ticker_vocab"):\n',
        1,
    ),
    (
        "test_equities_generator.py",
        '        # train + test partition the full set (temporal split, no overlap/loss).\n'
        '        assert arrays["X_train"].shape[0] + arrays["X_test"].shape[0] == n\n',
        '        # train + val + test partition the full set (temporal split, no overlap/loss).\n'
        '        # The default ratios are 0.8 / 0.1 / 0.1, so all three are non-empty here and\n'
        '        # the sum is exact rather than a lower bound.\n'
        '        assert arrays["X_val"].shape[0] > 0, "val partition must be non-empty"\n'
        '        assert arrays["X_train"].shape[0] + arrays["X_val"].shape[0] + arrays["X_test"].shape[0] == n\n',
        1,
    ),
    # Ordering: the no-future-leak claim is transitive across three partitions now.
    (
        "test_equities_generator.py",
        '    def test_temporal_split_ordering_per_ticker(self) -> None:\n'
        '        arrays = _generate(["AAPL", "MSFT"], {"AAPL": _ohlcv(seed=5), "MSFT": _ohlcv(seed=6)}, _shares(), train_ratio=0.7, test_ratio=0.3)\n'
        '        for code in range(len(arrays["ticker_vocab"])):\n'
        '            train_dates = arrays["date_train"][arrays["ticker_code_train"] == code]\n'
        '            test_dates = arrays["date_test"][arrays["ticker_code_test"] == code]\n'
        '            assert train_dates.max() <= test_dates.min(), "train must precede test"\n',
        '    def test_temporal_split_ordering_per_ticker(self) -> None:\n'
        '        arrays = _generate(["AAPL", "MSFT"], {"AAPL": _ohlcv(seed=5), "MSFT": _ohlcv(seed=6)}, _shares(), train_ratio=0.6, val_ratio=0.1, test_ratio=0.3)\n'
        '        for code in range(len(arrays["ticker_vocab"])):\n'
        '            per_split = {s: arrays[f"date_{s}"][arrays[f"ticker_code_{s}"] == code] for s in ("train", "val", "test")}\n'
        '            assert all(d.size for d in per_split.values()), "each partition must claim rows for every ticker"\n'
        '            # Transitive, not just train < test: checking the endpoints alone would\n'
        '            # leave val free to overlap either neighbour, and val is the split early\n'
        '            # stopping reads.\n'
        '            for earlier, later in (("train", "val"), ("val", "test"), ("train", "test")):\n'
        '                assert per_split[earlier].max() <= per_split[later].min(), f"{earlier} must precede {later}"\n',
        1,
    ),
    # The rejection message names three ratios; and the 0.1 val default now
    # participates, so a train+test pair that used to be legal is refused.
    (
        "test_equities_generator.py",
        '    def test_invalid_ratio_sum_rejected(self) -> None:\n'
        '        with pytest.raises(ValueError, match="train_ratio \\\\+ test_ratio"):\n'
        '            EquitiesParams(train_ratio=0.8, test_ratio=0.3)\n',
        '    def test_invalid_ratio_sum_rejected(self) -> None:\n'
        '        with pytest.raises(ValueError, match="train_ratio \\\\+ val_ratio \\\\+ test_ratio"):\n'
        '            EquitiesParams(train_ratio=0.8, test_ratio=0.3)\n'
        '\n'
        '    def test_default_val_ratio_participates_in_the_sum(self) -> None:\n'
        '        """0.7 + 0.3 was legal two-way and is refused three-way.\n'
        '\n'
        '        The validation share is not free: it comes out of the same 1.0. A caller\n'
        '        who wants the old two-way division has to say ``val_ratio=0.0`` and mean it,\n'
        '        rather than have the generator quietly shrink test to make room.\n'
        '        """\n'
        '        with pytest.raises(ValueError, match="train_ratio \\\\+ val_ratio \\\\+ test_ratio"):\n'
        '            EquitiesParams(train_ratio=0.7, test_ratio=0.3)\n'
        '        assert EquitiesParams(train_ratio=0.7, val_ratio=0.0, test_ratio=0.3).val_ratio == 0.0\n',
        1,
    ),
    # Rounding overshoot: three rounded counts, trimmed test-first.
    (
        "test_equities_generator.py",
        '    def test_generate_clips_test_split_when_rounding_overshoots(self) -> None:\n'
        '        # 8 business days condition to 7 rows; train=test=0.5 -> round(3.5)=4 each\n'
        '        # -> 4 + 4 > 7, exercising the ``n_test = n_rows - n_train`` clip.\n'
        '        arrays = _generate(["AAPL"], {"AAPL": _ohlcv(periods=8, seed=31)}, _shares(), train_ratio=0.5, test_ratio=0.5)\n'
        '        n = arrays["X_full"].shape[0]\n'
        '        assert n == 7\n'
        '        assert arrays["X_train"].shape[0] + arrays["X_test"].shape[0] == n\n',
        '    def test_generate_clips_test_split_when_rounding_overshoots(self) -> None:\n'
        '        # 8 business days condition to 7 rows; 0.5/0.25/0.25 rounds to 4 + 2 + 2 = 8\n'
        '        # against 7 rows, so one row of overflow has to be given back.\n'
        '        arrays = _generate(["AAPL"], {"AAPL": _ohlcv(periods=8, seed=31)}, _shares(), train_ratio=0.5, val_ratio=0.25, test_ratio=0.25)\n'
        '        n = arrays["X_full"].shape[0]\n'
        '        assert n == 7\n'
        '        assert arrays["X_train"].shape[0] + arrays["X_val"].shape[0] + arrays["X_test"].shape[0] == n\n'
        '        # Trimmed test-first, and train is never trimmed: shrinking train to fund a\n'
        '        # rounding artifact would change what the model was fit on, which is the one\n'
        '        # thing a split-arithmetic fix must not do.\n'
        '        assert arrays["X_train"].shape[0] == 4\n'
        '        assert arrays["X_val"].shape[0] == 2\n'
        '        assert arrays["X_test"].shape[0] == 1\n',
        1,
    ),
]


def _replace(path: pathlib.Path, old: str, new: str, expected: int) -> bool:
    src = path.read_text()
    found = src.count(old)
    if found != expected:
        print(f"{path.name}: matched {found}x, expected {expected} -- refusing:\n  {old.strip()[:100]}", file=sys.stderr)
        return False
    path.write_text(src.replace(old, new))
    return True


def main() -> int:
    ok = True
    for module in REGULAR_SEQ_MODULES:
        path = BASE / module
        ok &= _replace(path, SPLIT_LOOP_OLD, SPLIT_LOOP_NEW, 1)
        ok &= _replace(path, IDENTITY_OLD, IDENTITY_NEW, 1)
    for filename, old, new, expected in EDITS:
        ok &= _replace(BASE / filename, old, new, expected)
    print("done" if ok else "INCOMPLETE -- see refusals above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
