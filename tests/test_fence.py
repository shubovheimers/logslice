"""Tests for logslice.fence."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.fence import FenceOptions, fence_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=None, level=None, message=text, extra={})


def collect(lines, opts):
    return [l.raw for l in fence_lines(lines, opts)]


class TestFenceOptions:
    def test_missing_start_raises(self):
        with pytest.raises(ValueError):
            FenceOptions(start_pattern="", end_pattern="END")

    def test_missing_end_raises(self):
        with pytest.raises(ValueError):
            FenceOptions(start_pattern="START", end_pattern="")

    def test_enabled_with_both(self):
        opts = FenceOptions(start_pattern="S", end_pattern="E")
        assert opts.enabled()


class TestFenceLines:
    LINES = [
        "before",
        "START here",
        "inside one",
        "inside two",
        "END here",
        "after",
    ]

    def _lines(self):
        return [make_line(t) for t in self.LINES]

    def test_inclusive_default(self):
        opts = FenceOptions(start_pattern="START", end_pattern="END")
        result = collect(self._lines(), opts)
        assert result == ["START here", "inside one", "inside two", "END here"]

    def test_exclusive_boundaries(self):
        opts = FenceOptions(start_pattern="START", end_pattern="END", inclusive=False)
        result = collect(self._lines(), opts)
        assert result == ["inside one", "inside two"]

    def test_before_and_after_excluded(self):
        opts = FenceOptions(start_pattern="START", end_pattern="END")
        result = collect(self._lines(), opts)
        assert "before" not in result
        assert "after" not in result

    def test_no_match_yields_nothing(self):
        opts = FenceOptions(start_pattern="NOPE", end_pattern="END")
        result = collect(self._lines(), opts)
        assert result == []

    def test_repeat_captures_multiple_regions(self):
        lines = [
            make_line("START"),
            make_line("a"),
            make_line("END"),
            make_line("middle"),
            make_line("START"),
            make_line("b"),
            make_line("END"),
        ]
        opts = FenceOptions(start_pattern="START", end_pattern="END", repeat=True)
        result = collect(lines, opts)
        assert "a" in result and "b" in result
        assert "middle" not in result

    def test_repeat_false_stops_after_first_region(self):
        lines = [
            make_line("START"),
            make_line("a"),
            make_line("END"),
            make_line("START"),
            make_line("b"),
            make_line("END"),
        ]
        opts = FenceOptions(start_pattern="START", end_pattern="END", repeat=False)
        result = collect(lines, opts)
        assert "a" in result
        assert "b" not in result

    def test_case_insensitive_default(self):
        lines = [make_line("start"), make_line("x"), make_line("end")]
        opts = FenceOptions(start_pattern="START", end_pattern="END")
        result = collect(lines, opts)
        assert "x" in result
