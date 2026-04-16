"""Tests for logslice.windower."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from logslice.parser import LogLine
from logslice.windower import WindowOptions, Window, window_lines


def make_line(ts: datetime, text: str = "msg") -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text, extra={})


def dt(second: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, second, tzinfo=timezone.utc)


class TestWindowOptions:
    def test_defaults_not_enabled(self):
        opts = WindowOptions()
        assert not opts.enabled

    def test_invalid_size_raises(self):
        with pytest.raises(ValueError):
            WindowOptions(enabled=True, size_seconds=0)

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError):
            WindowOptions(enabled=True, size_seconds=10, step_seconds=-1)

    def test_sliding_when_step_set(self):
        opts = WindowOptions(enabled=True, size_seconds=60, step_seconds=30)
        assert opts.is_sliding

    def test_tumbling_when_no_step(self):
        opts = WindowOptions(enabled=True, size_seconds=60)
        assert not opts.is_sliding


class TestWindowLines:
    def _opts(self, size=60, step=None, min_lines=1):
        return WindowOptions(enabled=True, size_seconds=size, step_seconds=step, min_lines=min_lines)

    def test_disabled_yields_nothing(self):
        opts = WindowOptions(enabled=False, size_seconds=10)
        lines = [make_line(dt(0)), make_line(dt(5))]
        assert list(window_lines(iter(lines), opts)) == []

    def test_empty_input_yields_nothing(self):
        opts = self._opts(size=10)
        assert list(window_lines(iter([]), opts)) == []

    def test_lines_without_timestamp_skipped(self):
        opts = self._opts(size=10)
        no_ts = LogLine(raw="x", timestamp=None, level=None, message="x", extra={})
        assert list(window_lines(iter([no_ts]), opts)) == []

    def test_tumbling_single_window(self):
        opts = self._opts(size=10)
        lines = [make_line(dt(0)), make_line(dt(5)), make_line(dt(9))]
        windows = list(window_lines(iter(lines), opts))
        assert len(windows) == 1
        assert len(windows[0]) == 3

    def test_tumbling_two_windows(self):
        opts = self._opts(size=10)
        lines = [make_line(dt(0)), make_line(dt(5)), make_line(dt(10)), make_line(dt(15))]
        windows = list(window_lines(iter(lines), opts))
        assert len(windows) == 2

    def test_min_lines_filters_sparse_windows(self):
        opts = self._opts(size=10, min_lines=3)
        lines = [make_line(dt(0)), make_line(dt(5))]  # only 2 in window
        windows = list(window_lines(iter(lines), opts))
        assert windows == []

    def test_window_start_end_set(self):
        opts = self._opts(size=10)
        lines = [make_line(dt(0)), make_line(dt(5))]
        w = list(window_lines(iter(lines), opts))[0]
        assert w.start == dt(0)
        assert w.end == dt(10)

    def test_sliding_produces_more_windows_than_tumbling(self):
        lines = [make_line(dt(i * 5)) for i in range(6)]  # 0,5,10,15,20,25
        tumbling = list(window_lines(iter(lines), self._opts(size=20)))
        sliding = list(window_lines(iter(lines), self._opts(size=20, step=5)))
        assert len(sliding) >= len(tumbling)
