"""Tests for logslice.shifter."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from logslice.parser import LogLine
from logslice.shifter import ShiftOptions, shift_lines


def make_line(ts: datetime | None = None, msg: str = "hello") -> LogLine:
    return LogLine(
        raw=msg,
        timestamp=ts,
        level="INFO",
        message=msg,
        extra={},
    )


DT = datetime(2024, 1, 15, 12, 0, 0)


class TestShiftOptions:
    def test_defaults_not_enabled(self):
        opts = ShiftOptions()
        assert not opts.enabled

    def test_seconds_enables(self):
        opts = ShiftOptions(seconds=30)
        assert opts.enabled

    def test_negative_hours_enables(self):
        opts = ShiftOptions(hours=-2)
        assert opts.enabled

    def test_delta_combines_all_fields(self):
        opts = ShiftOptions(days=1, hours=2, minutes=3, seconds=4)
        expected = timedelta(days=1, hours=2, minutes=3, seconds=4)
        assert opts.delta == expected


class TestShiftLines:
    def test_passthrough_when_opts_none(self):
        lines = [make_line(DT), make_line(DT)]
        result = list(shift_lines(lines, None))
        assert result == lines

    def test_passthrough_when_disabled(self):
        opts = ShiftOptions()  # zero delta
        lines = [make_line(DT)]
        result = list(shift_lines(lines, opts))
        assert result[0].timestamp == DT

    def test_forward_shift_seconds(self):
        opts = ShiftOptions(seconds=90)
        line = make_line(DT)
        result = list(shift_lines([line], opts))
        assert result[0].timestamp == DT + timedelta(seconds=90)

    def test_backward_shift_hours(self):
        opts = ShiftOptions(hours=-3)
        line = make_line(DT)
        result = list(shift_lines([line], opts))
        assert result[0].timestamp == DT - timedelta(hours=3)

    def test_line_without_timestamp_unchanged(self):
        opts = ShiftOptions(minutes=10)
        line = make_line(ts=None, msg="no ts")
        result = list(shift_lines([line], opts))
        assert result[0].timestamp is None
        assert result[0].raw == "no ts"

    def test_raw_and_level_preserved(self):
        opts = ShiftOptions(days=1)
        line = make_line(DT, msg="keep me")
        result = list(shift_lines([line], opts))
        assert result[0].raw == "keep me"
        assert result[0].level == "INFO"

    def test_multiple_lines_all_shifted(self):
        opts = ShiftOptions(seconds=60)
        times = [datetime(2024, 1, 1, 0, i, 0) for i in range(5)]
        lines = [make_line(t) for t in times]
        result = list(shift_lines(lines, opts))
        for original, shifted in zip(times, result):
            assert shifted.timestamp == original + timedelta(seconds=60)
