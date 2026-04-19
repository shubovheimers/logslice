"""Tests for logslice.slicer."""
from __future__ import annotations

import pytest
from datetime import datetime
from logslice.parser import LogLine
from logslice.slicer import SliceOptions, slice_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=None, level=None, message=text, extra={})


def make_lines(n: int) -> list[LogLine]:
    return [make_line(f"line {i}") for i in range(n)]


class TestSliceOptions:
    def test_defaults_not_enabled(self):
        assert not SliceOptions().enabled

    def test_start_enables(self):
        assert SliceOptions(start_line=3).enabled

    def test_end_enables(self):
        assert SliceOptions(end_line=10).enabled

    def test_step_enables(self):
        assert SliceOptions(step=2).enabled

    def test_negative_start_raises(self):
        with pytest.raises(ValueError, match="start_line"):
            SliceOptions(start_line=-1)

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError, match="end_line"):
            SliceOptions(start_line=5, end_line=3)

    def test_zero_step_raises(self):
        with pytest.raises(ValueError, match="step"):
            SliceOptions(step=0)


class TestSliceLines:
    def test_passthrough_when_none(self):
        lines = make_lines(5)
        assert list(slice_lines(lines, None)) == lines

    def test_passthrough_when_not_enabled(self):
        lines = make_lines(5)
        assert list(slice_lines(lines, SliceOptions())) == lines

    def test_start_only(self):
        lines = make_lines(6)
        result = list(slice_lines(lines, SliceOptions(start_line=3)))
        assert result == lines[3:]

    def test_end_only(self):
        lines = make_lines(6)
        result = list(slice_lines(lines, SliceOptions(end_line=4)))
        assert result == lines[:4]

    def test_start_and_end(self):
        lines = make_lines(10)
        result = list(slice_lines(lines, SliceOptions(start_line=2, end_line=7)))
        assert result == lines[2:7]

    def test_step_2(self):
        lines = make_lines(8)
        result = list(slice_lines(lines, SliceOptions(step=2)))
        assert result == lines[::2]

    def test_start_and_step(self):
        lines = make_lines(10)
        result = list(slice_lines(lines, SliceOptions(start_line=1, step=3)))
        assert [l.raw for l in result] == ["line 1", "line 4", "line 7"]

    def test_empty_input(self):
        assert list(slice_lines([], SliceOptions(start_line=0, end_line=5))) == []

    def test_end_beyond_length(self):
        lines = make_lines(3)
        result = list(slice_lines(lines, SliceOptions(end_line=100)))
        assert result == lines
