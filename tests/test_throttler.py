"""Tests for logslice.throttler."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.throttler import ThrottleOptions, throttle_lines, _Window


def make_line(text: str = "msg", ts: datetime | None = None) -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text)


def lines_at(times: List[datetime]) -> List[LogLine]:
    return [make_line(f"line-{i}", ts=t) for i, t in enumerate(times)]


# ---------------------------------------------------------------------------
# ThrottleOptions
# ---------------------------------------------------------------------------

class TestThrottleOptions:
    def test_disabled_by_default(self):
        opts = ThrottleOptions()
        assert not opts.enabled()

    def test_enabled_when_max_lines_set(self):
        opts = ThrottleOptions(max_lines=5)
        assert opts.enabled()

    def test_disabled_when_window_zero(self):
        opts = ThrottleOptions(max_lines=5, window_seconds=0)
        assert not opts.enabled()

    def test_disabled_when_max_lines_zero(self):
        opts = ThrottleOptions(max_lines=0, window_seconds=1.0)
        assert not opts.enabled()


# ---------------------------------------------------------------------------
# _Window
# ---------------------------------------------------------------------------

class TestWindow:
    def test_allows_up_to_max(self):
        w = _Window(size=timedelta(seconds=1), max_lines=3)
        t = datetime(2024, 1, 1, 12, 0, 0)
        assert w.allow(t) is True
        assert w.allow(t) is True
        assert w.allow(t) is True
        assert w.allow(t) is False  # 4th within same second

    def test_evicts_old_entries(self):
        w = _Window(size=timedelta(seconds=1), max_lines=2)
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        t1 = t0 + timedelta(seconds=2)  # outside window
        w.allow(t0)
        w.allow(t0)
        # window has rolled; old entries evicted
        assert w.allow(t1) is True


# ---------------------------------------------------------------------------
# throttle_lines
# ---------------------------------------------------------------------------

class TestThrottleLines:
    def test_passthrough_when_opts_none(self):
        src = [make_line("a"), make_line("b")]
        result = list(throttle_lines(src, None))
        assert result == src

    def test_passthrough_when_disabled(self):
        opts = ThrottleOptions(max_lines=0)
        src = [make_line("a"), make_line("b")]
        result = list(throttle_lines(src, opts))
        assert result == src

    def test_limits_lines_in_window(self):
        t = datetime(2024, 6, 1, 0, 0, 0)
        src = lines_at([t, t, t, t, t])  # 5 lines same second
        opts = ThrottleOptions(max_lines=3, window_seconds=1.0)
        result = list(throttle_lines(src, opts))
        assert len(result) == 3

    def test_allows_lines_in_next_window(self):
        t0 = datetime(2024, 6, 1, 0, 0, 0)
        t1 = t0 + timedelta(seconds=2)
        src = lines_at([t0, t0, t0, t1, t1])
        opts = ThrottleOptions(max_lines=2, window_seconds=1.0)
        result = list(throttle_lines(src, opts))
        # 2 from first burst + 2 from second burst
        assert len(result) == 4

    def test_empty_input_returns_empty(self):
        opts = ThrottleOptions(max_lines=10)
        result = list(throttle_lines([], opts))
        assert result == []
