"""Integration tests for time-based log slicing."""
from __future__ import annotations

from datetime import datetime, timedelta

from logslice.parser import LogLine
from logslice.splitter_time import TimeSliceOptions, slice_by_time


def _line(offset_s: int, level: str = "INFO") -> LogLine:
    ts = datetime(2024, 3, 15, 8, 0, 0) + timedelta(seconds=offset_s)
    text = f"{ts.isoformat()} {level} message at +{offset_s}s"
    return LogLine(raw=text, timestamp=ts, level=level, message=text, extra={})


class TestSplitterTimeIntegration:
    def test_total_lines_preserved(self):
        lines = [_line(i * 10) for i in range(30)]  # 300 s span, 60s window -> 5 slices
        opts = TimeSliceOptions(window_seconds=60)
        slices = list(slice_by_time(iter(lines), opts))
        total = sum(len(s) for s in slices)
        assert total == 30

    def test_correct_number_of_slices(self):
        lines = [_line(i * 10) for i in range(30)]
        opts = TimeSliceOptions(window_seconds=60)
        slices = list(slice_by_time(iter(lines), opts))
        assert len(slices) == 5

    def test_each_line_in_correct_window(self):
        lines = [_line(i * 10) for i in range(30)]
        opts = TimeSliceOptions(window_seconds=60)
        for slc in slice_by_time(iter(lines), opts):
            for ln in slc.lines:
                assert slc.start <= ln.timestamp < slc.end

    def test_mixed_levels_all_included(self):
        levels = ["INFO", "ERROR", "WARN"]
        lines = [_line(i * 5, levels[i % 3]) for i in range(12)]
        opts = TimeSliceOptions(window_seconds=30)
        slices = list(slice_by_time(iter(lines), opts))
        all_levels = {ln.level for s in slices for ln in s.lines}
        assert all_levels == {"INFO", "ERROR", "WARN"}
