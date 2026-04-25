"""Tests for logslice.clamper_time."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.clamper_time import ClampTimeOptions, clamp_time_lines


def make_line(ts: datetime | None = None, msg: str = "hello") -> LogLine:
    return LogLine(raw=msg, timestamp=ts, level=None, message=msg, extra={})


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


def collect(lines, opts) -> List[LogLine]:
    return list(clamp_time_lines(lines, opts))


# ---------------------------------------------------------------------------
# ClampTimeOptions
# ---------------------------------------------------------------------------

class TestClampTimeOptions:
    def test_defaults_not_active(self):
        assert not ClampTimeOptions().is_active

    def test_floor_activates(self):
        assert ClampTimeOptions(floor=dt(8)).is_active

    def test_ceiling_activates(self):
        assert ClampTimeOptions(ceiling=dt(18)).is_active

    def test_floor_after_ceiling_raises(self):
        with pytest.raises(ValueError, match="floor"):
            ClampTimeOptions(floor=dt(18), ceiling=dt(8))

    def test_equal_floor_and_ceiling_ok(self):
        opts = ClampTimeOptions(floor=dt(12), ceiling=dt(12))
        assert opts.is_active


# ---------------------------------------------------------------------------
# clamp_time_lines – passthrough
# ---------------------------------------------------------------------------

class TestClampTimeLinesPassthrough:
    def test_none_opts_passthrough(self):
        lines = [make_line(dt(6)), make_line(dt(12))]
        assert collect(lines, None) == lines

    def test_inactive_opts_passthrough(self):
        lines = [make_line(dt(6)), make_line(dt(12))]
        assert collect(lines, ClampTimeOptions()) == lines

    def test_no_timestamp_always_yielded(self):
        lines = [make_line(None)]
        opts = ClampTimeOptions(floor=dt(8), ceiling=dt(18))
        result = collect(lines, opts)
        assert len(result) == 1
        assert result[0].timestamp is None


# ---------------------------------------------------------------------------
# clamp_time_lines – replace with boundary (default)
# ---------------------------------------------------------------------------

class TestClampTimeReplace:
    def test_below_floor_replaced(self):
        opts = ClampTimeOptions(floor=dt(8))
        line = make_line(dt(6))
        result = collect([line], opts)
        assert result[0].timestamp == dt(8)

    def test_above_ceiling_replaced(self):
        opts = ClampTimeOptions(ceiling=dt(18))
        line = make_line(dt(20))
        result = collect([line], opts)
        assert result[0].timestamp == dt(18)

    def test_within_range_unchanged(self):
        opts = ClampTimeOptions(floor=dt(8), ceiling=dt(18))
        line = make_line(dt(12))
        result = collect([line], opts)
        assert result[0].timestamp == dt(12)

    def test_other_fields_preserved(self):
        opts = ClampTimeOptions(floor=dt(8))
        line = make_line(dt(6), msg="important")
        result = collect([line], opts)
        assert result[0].message == "important"
        assert result[0].raw == "important"


# ---------------------------------------------------------------------------
# clamp_time_lines – drop out of range
# ---------------------------------------------------------------------------

class TestClampTimeDrop:
    def test_below_floor_dropped(self):
        opts = ClampTimeOptions(floor=dt(8), drop_out_of_range=True)
        lines = [make_line(dt(6)), make_line(dt(10))]
        result = collect(lines, opts)
        assert len(result) == 1
        assert result[0].timestamp == dt(10)

    def test_above_ceiling_dropped(self):
        opts = ClampTimeOptions(ceiling=dt(18), drop_out_of_range=True)
        lines = [make_line(dt(20)), make_line(dt(12))]
        result = collect(lines, opts)
        assert len(result) == 1
        assert result[0].timestamp == dt(12)

    def test_all_in_range_none_dropped(self):
        opts = ClampTimeOptions(floor=dt(8), ceiling=dt(18), drop_out_of_range=True)
        lines = [make_line(dt(9)), make_line(dt(12)), make_line(dt(17))]
        assert len(collect(lines, opts)) == 3
