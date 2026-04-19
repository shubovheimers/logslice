"""Tests for logslice.splitter_time."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.splitter_time import TimeSlice, TimeSliceOptions, slice_by_time


def make_line(ts: datetime | None = None, text: str = "msg") -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text, extra={})


def _dt(offset_s: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, 0) + timedelta(seconds=offset_s)


class TestTimeSliceOptions:
    def test_defaults(self):
        opts = TimeSliceOptions()
        assert opts.window_seconds == 3600
        assert opts.drop_empty is True

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            TimeSliceOptions(window_seconds=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError):
            TimeSliceOptions(window_seconds=-10)


class TestSliceByTime:
    def test_empty_input_yields_nothing(self):
        opts = TimeSliceOptions(window_seconds=60)
        result = list(slice_by_time(iter([]), opts))
        assert result == []

    def test_single_line_single_slice(self):
        opts = TimeSliceOptions(window_seconds=60)
        lines = [make_line(_dt(0))]
        slices = list(slice_by_time(iter(lines), opts))
        assert len(slices) == 1
        assert len(slices[0]) == 1

    def test_lines_in_same_window_grouped(self):
        opts = TimeSliceOptions(window_seconds=60)
        lines = [make_line(_dt(i)) for i in range(10)]
        slices = list(slice_by_time(iter(lines), opts))
        assert len(slices) == 1
        assert len(slices[0]) == 10

    def test_lines_split_across_windows(self):
        opts = TimeSliceOptions(window_seconds=60)
        lines = [make_line(_dt(0)), make_line(_dt(61)), make_line(_dt(122))]
        slices = list(slice_by_time(iter(lines), opts))
        assert len(slices) == 3
        assert all(len(s) == 1 for s in slices)

    def test_no_timestamp_lines_appended_to_current_bucket(self):
        opts = TimeSliceOptions(window_seconds=60)
        lines = [make_line(_dt(0)), make_line(None, "no-ts"), make_line(_dt(10))]
        slices = list(slice_by_time(iter(lines), opts))
        assert len(slices) == 1
        assert len(slices[0]) == 3

    def test_drop_empty_default(self):
        opts = TimeSliceOptions(window_seconds=60)
        # Two lines 200 s apart — middle window is empty
        lines = [make_line(_dt(0)), make_line(_dt(200))]
        slices = list(slice_by_time(iter(lines), opts))
        # Only non-empty slices returned
        assert all(len(s) > 0 for s in slices)

    def test_slice_start_end_correct(self):
        opts = TimeSliceOptions(window_seconds=100)
        base = datetime(2024, 6, 1, 12, 0, 0)
        lines = [make_line(base + timedelta(seconds=5))]
        slices = list(slice_by_time(iter(lines), opts))
        assert slices[0].start == base
        assert slices[0].end == base + timedelta(seconds=100)

    def test_len_dunder(self):
        s = TimeSlice(start=_dt(0), end=_dt(60), lines=[make_line(_dt(1))])
        assert len(s) == 1
