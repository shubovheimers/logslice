"""Tests for logslice.spinner."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.spinner import SpinOptions, SpinWindow, spin_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, text=text, timestamp=datetime(2024, 1, 1), level=None, extra={})


def make_lines(n: int) -> List[LogLine]:
    return [make_line(f"line {i}") for i in range(n)]


class TestSpinOptions:
    def test_defaults_not_enabled(self):
        assert SpinOptions().enabled is False

    def test_size_enables(self):
        assert SpinOptions(size=3).enabled is True

    def test_negative_size_raises(self):
        with pytest.raises(ValueError, match="size"):
            SpinOptions(size=-1)

    def test_step_zero_raises(self):
        with pytest.raises(ValueError, match="step"):
            SpinOptions(size=2, step=0)

    def test_step_negative_raises(self):
        with pytest.raises(ValueError, match="step"):
            SpinOptions(size=2, step=-1)


class TestSpinLines:
    def test_disabled_yields_all_in_one_window(self):
        lines = make_lines(5)
        windows = list(spin_lines(lines, SpinOptions()))
        assert len(windows) == 1
        assert len(windows[0]) == 5

    def test_empty_source_disabled(self):
        windows = list(spin_lines([], SpinOptions()))
        assert len(windows) == 1
        assert len(windows[0]) == 0

    def test_exact_size_yields_one_window(self):
        lines = make_lines(3)
        windows = list(spin_lines(lines, SpinOptions(size=3)))
        assert len(windows) == 1
        assert len(windows[0]) == 3

    def test_multiple_windows_step_1(self):
        lines = make_lines(5)
        opts = SpinOptions(size=3, step=1)
        windows = list(spin_lines(lines, opts))
        # windows at positions 0,1,2 (lines 0-2, 1-3, 2-4)
        assert len(windows) == 3
        assert [w.lines[0].text for w in windows] == ["line 0", "line 1", "line 2"]

    def test_step_2_skips_windows(self):
        lines = make_lines(6)
        opts = SpinOptions(size=3, step=2)
        windows = list(spin_lines(lines, opts))
        assert len(windows) == 2

    def test_window_index_increments(self):
        lines = make_lines(6)
        opts = SpinOptions(size=2, step=2)
        windows = list(spin_lines(lines, opts))
        assert [w.index for w in windows] == [0, 1, 2]

    def test_partial_false_no_trailing(self):
        lines = make_lines(5)
        opts = SpinOptions(size=3, step=3, partial=False)
        windows = list(spin_lines(lines, opts))
        # only one full window of 3
        assert len(windows) == 1

    def test_partial_true_emits_trailing(self):
        lines = make_lines(5)
        opts = SpinOptions(size=3, step=3, partial=True)
        windows = list(spin_lines(lines, opts))
        assert len(windows) == 2
        assert len(windows[-1]) <= 3

    def test_window_len(self):
        w = SpinWindow(lines=make_lines(4), index=0)
        assert len(w) == 4
