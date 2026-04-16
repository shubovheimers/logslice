"""Tests for logslice.sorter."""
from __future__ import annotations

import pytest
from datetime import datetime
from typing import Optional

from logslice.parser import LogLine
from logslice.sorter import SortOptions, sort_lines, LEVEL_ORDER


def make_line(
    raw: str = "msg",
    ts: Optional[datetime] = None,
    level: Optional[str] = None,
    lineno: int = 0,
) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw, lineno=lineno)


dt = datetime


class TestSortOptions:
    def test_default_by_timestamp(self):
        assert SortOptions().by == "timestamp"

    def test_invalid_by_raises(self):
        with pytest.raises(ValueError):
            SortOptions(by="banana")

    def test_enabled_always_true(self):
        assert SortOptions().enabled()


class TestSortByTimestamp:
    def _lines(self):
        return [
            make_line("c", dt(2024, 1, 1, 12, 0, 0), lineno=3),
            make_line("a", dt(2024, 1, 1, 10, 0, 0), lineno=1),
            make_line("b", dt(2024, 1, 1, 11, 0, 0), lineno=2),
        ]

    def test_ascending(self):
        opts = SortOptions(by="timestamp")
        result = list(sort_lines(self._lines(), opts))
        assert [l.raw for l in result] == ["a", "b", "c"]

    def test_descending(self):
        opts = SortOptions(by="timestamp", reverse=True)
        result = list(sort_lines(self._lines(), opts))
        assert [l.raw for l in result] == ["c", "b", "a"]

    def test_none_timestamp_sorted_last(self):
        lines = [
            make_line("no-ts", ts=None),
            make_line("has-ts", ts=dt(2024, 1, 1)),
        ]
        result = list(sort_lines(lines, SortOptions(by="timestamp")))
        assert result[0].raw == "has-ts"
        assert result[1].raw == "no-ts"


class TestSortByLevel:
    def test_ascending_level_order(self):
        lines = [
            make_line("e", level="error"),
            make_line("d", level="debug"),
            make_line("i", level="info"),
        ]
        result = list(sort_lines(lines, SortOptions(by="level")))
        assert [l.raw for l in result] == ["d", "i", "e"]

    def test_unknown_level_first(self):
        lines = [
            make_line("i", level="info"),
            make_line("u", level="unknown"),
        ]
        result = list(sort_lines(lines, SortOptions(by="level")))
        assert result[0].raw == "u"


class TestSortByLineno:
    def test_lineno_order(self):
        lines = [make_line(str(n), lineno=n) for n in [3, 1, 2]]
        result = list(sort_lines(lines, SortOptions(by="lineno")))
        assert [l.lineno for l in result] == [1, 2, 3]


class TestBufferedSort:
    def test_chunked_sort(self):
        lines = [make_line(str(n), ts=dt(2024, 1, 1, n, 0)) for n in [3, 1, 2, 6, 4, 5]]
        opts = SortOptions(by="timestamp", buffer_size=3)
        result = list(sort_lines(lines, opts))
        # Each chunk of 3 is sorted independently
        assert [l.raw for l in result] == ["1", "2", "3", "4", "5", "6"]


class TestNoOpts:
    def test_passthrough_when_none(self):
        lines = [make_line(str(n)) for n in [3, 1, 2]]
        result = list(sort_lines(lines, None))
        assert [l.raw for l in result] == ["3", "1", "2"]
