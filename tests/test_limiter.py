"""Tests for logslice.limiter."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from logslice.parser import LogLine
from logslice.limiter import LimitOptions, limit_lines


def make_line(text: str = "msg", ts: datetime | None = None) -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text, extra={})


def dt(offset: float = 0.0) -> datetime:
    base = datetime(2024, 1, 1, 12, 0, 0)
    return base + timedelta(seconds=offset)


# ---------------------------------------------------------------------------
# LimitOptions
# ---------------------------------------------------------------------------

class TestLimitOptions:
    def test_defaults_not_enabled(self):
        assert not LimitOptions().enabled

    def test_max_lines_enables(self):
        assert LimitOptions(max_lines=5).enabled

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            LimitOptions(max_lines=-1)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            LimitOptions(max_lines=1, window_seconds=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            LimitOptions(max_lines=1, window_seconds=-5)


# ---------------------------------------------------------------------------
# limit_lines
# ---------------------------------------------------------------------------

class TestLimitLines:
    def test_disabled_passes_all(self):
        lines = [make_line(ts=dt(i)) for i in range(10)]
        result = list(limit_lines(lines, LimitOptions(max_lines=0)))
        assert len(result) == 10

    def test_none_opts_passes_all(self):
        lines = [make_line(ts=dt(i)) for i in range(5)]
        assert list(limit_lines(lines, None)) == lines

    def test_caps_within_window(self):
        # 5 lines in the same second, cap at 2
        lines = [make_line(ts=dt(0)) for _ in range(5)]
        result = list(limit_lines(lines, LimitOptions(max_lines=2, window_seconds=1)))
        assert len(result) == 2

    def test_new_window_resets_count(self):
        # 3 lines at t=0, 3 lines at t=2 — window=1s, max=2
        lines = [make_line(ts=dt(0)) for _ in range(3)] + \
                [make_line(ts=dt(2)) for _ in range(3)]
        result = list(limit_lines(lines, LimitOptions(max_lines=2, window_seconds=1)))
        assert len(result) == 4  # 2 from each window

    def test_lines_without_timestamp_always_pass(self):
        lines = [make_line(ts=None) for _ in range(10)]
        result = list(limit_lines(lines, LimitOptions(max_lines=1, window_seconds=1)))
        assert len(result) == 10

    def test_exact_limit_all_pass(self):
        lines = [make_line(ts=dt(0)) for _ in range(3)]
        result = list(limit_lines(lines, LimitOptions(max_lines=3, window_seconds=1)))
        assert len(result) == 3

    def test_mixed_timestamps_across_windows(self):
        # window=5s, max=2; lines at 0,1,2,5,6,7
        times = [0, 1, 2, 5, 6, 7]
        lines = [make_line(ts=dt(t)) for t in times]
        result = list(limit_lines(lines, LimitOptions(max_lines=2, window_seconds=5)))
        # window1: t0,t1 pass; t2 dropped. window2: t5,t6 pass; t7 dropped
        assert len(result) == 4
        assert result[0].timestamp == dt(0)
        assert result[1].timestamp == dt(1)
        assert result[2].timestamp == dt(5)
        assert result[3].timestamp == dt(6)
