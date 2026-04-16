"""Tests for logslice.batcher."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest

from logslice.batcher import BatchOptions, batch_lines
from logslice.parser import LogLine


def make_line(text: str = "msg", ts: datetime | None = None) -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text, extra={})


def dt(offset_s: float) -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_s)


def collect(lines, opts) -> List[List[LogLine]]:
    return list(batch_lines(lines, opts))


# ---------------------------------------------------------------------------
# BatchOptions validation
# ---------------------------------------------------------------------------

class TestBatchOptions:
    def test_defaults_not_enabled(self):
        assert not BatchOptions().enabled()

    def test_size_enables(self):
        assert BatchOptions(size=5).enabled()

    def test_window_enables(self):
        assert BatchOptions(window_seconds=10.0).enabled()

    def test_negative_size_raises(self):
        with pytest.raises(ValueError):
            BatchOptions(size=-1)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError):
            BatchOptions(window_seconds=-0.1)


# ---------------------------------------------------------------------------
# batch_lines – disabled
# ---------------------------------------------------------------------------

class TestBatchDisabled:
    def test_each_line_is_own_batch(self):
        lines = [make_line(f"l{i}") for i in range(4)]
        batches = collect(lines, BatchOptions())
        assert len(batches) == 4
        assert all(len(b) == 1 for b in batches)

    def test_empty_input(self):
        assert collect([], BatchOptions()) == []


# ---------------------------------------------------------------------------
# batch_lines – size-based
# ---------------------------------------------------------------------------

class TestBatchBySize:
    def test_exact_multiple(self):
        lines = [make_line(f"l{i}") for i in range(6)]
        batches = collect(lines, BatchOptions(size=3))
        assert len(batches) == 2
        assert all(len(b) == 3 for b in batches)

    def test_remainder_flushed(self):
        lines = [make_line(f"l{i}") for i in range(5)]
        batches = collect(lines, BatchOptions(size=3))
        assert len(batches) == 2
        assert len(batches[-1]) == 2

    def test_single_line_batch(self):
        lines = [make_line("only")]
        batches = collect(lines, BatchOptions(size=10))
        assert batches == [[lines[0]]]


# ---------------------------------------------------------------------------
# batch_lines – time-window-based
# ---------------------------------------------------------------------------

class TestBatchByWindow:
    def test_window_splits_on_boundary(self):
        lines = [
            make_line("a", dt(0)),
            make_line("b", dt(4)),
            make_line("c", dt(10)),   # 10s from start -> flush
            make_line("d", dt(11)),
        ]
        batches = collect(lines, BatchOptions(window_seconds=10))
        assert len(batches) == 2
        assert len(batches[0]) == 2   # a, b
        assert len(batches[1]) == 2   # c, d

    def test_no_timestamps_no_split(self):
        lines = [make_line(f"l{i}") for i in range(6)]
        batches = collect(lines, BatchOptions(window_seconds=1))
        assert len(batches) == 1
        assert len(batches[0]) == 6

    def test_empty_input(self):
        assert collect([], BatchOptions(window_seconds=5)) == []
