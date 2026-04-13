"""Tests for logslice.context."""

from datetime import datetime
from typing import List

import pytest

from logslice.context import ContextOptions, iter_with_context
from logslice.parser import LogLine


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
    )


LINES: List[LogLine] = [make_line(f"line{i}") for i in range(10)]


def is_line5(line: LogLine) -> bool:
    return line.raw == "line5"


class TestContextOptions:
    def test_disabled_when_both_zero(self):
        assert not ContextOptions(before=0, after=0).enabled

    def test_enabled_with_before(self):
        assert ContextOptions(before=2).enabled

    def test_enabled_with_after(self):
        assert ContextOptions(after=1).enabled


class TestIterWithContextDisabled:
    def test_no_context_returns_only_matches(self):
        opts = ContextOptions(before=0, after=0)
        result = list(iter_with_context(LINES, is_line5, opts))
        assert len(result) == 1
        assert result[0].raw == "line5"

    def test_no_matches_returns_empty(self):
        opts = ContextOptions(before=0, after=0)
        result = list(iter_with_context(LINES, lambda l: False, opts))
        assert result == []


class TestBeforeContext:
    def test_before_2_includes_preceding_lines(self):
        opts = ContextOptions(before=2, after=0)
        result = list(iter_with_context(LINES, is_line5, opts))
        raws = [l.raw for l in result]
        assert raws == ["line3", "line4", "line5"]

    def test_before_larger_than_available(self):
        is_line1 = lambda l: l.raw == "line1"
        opts = ContextOptions(before=5, after=0)
        result = list(iter_with_context(LINES, is_line1, opts))
        raws = [l.raw for l in result]
        assert raws == ["line0", "line1"]


class TestAfterContext:
    def test_after_2_includes_following_lines(self):
        opts = ContextOptions(before=0, after=2)
        result = list(iter_with_context(LINES, is_line5, opts))
        raws = [l.raw for l in result]
        assert raws == ["line5", "line6", "line7"]

    def test_after_at_end_of_file(self):
        is_last = lambda l: l.raw == "line9"
        opts = ContextOptions(before=0, after=3)
        result = list(iter_with_context(LINES, is_last, opts))
        raws = [l.raw for l in result]
        assert raws == ["line9"]


class TestCombinedContext:
    def test_before_and_after(self):
        opts = ContextOptions(before=1, after=1)
        result = list(iter_with_context(LINES, is_line5, opts))
        raws = [l.raw for l in result]
        assert raws == ["line4", "line5", "line6"]

    def test_overlapping_windows_no_duplicates(self):
        is_3_or_5 = lambda l: l.raw in ("line3", "line5")
        opts = ContextOptions(before=1, after=2)
        result = list(iter_with_context(LINES, is_3_or_5, opts))
        raws = [l.raw for l in result]
        # line2(before3), line3, line4(after3/before5), line5, line6, line7
        assert raws == ["line2", "line3", "line4", "line5", "line6", "line7"]
        assert len(raws) == len(set(raws))
