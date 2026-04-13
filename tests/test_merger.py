"""Tests for logslice.merger."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.merger import MergeOptions, merge_logs
from logslice.parser import LogLine


def make_line(raw: str, ts: datetime | None = None, level: str | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw)


T = datetime  # shorthand


def dt(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second)


# ---------------------------------------------------------------------------
# Basic ordering
# ---------------------------------------------------------------------------

class TestMergeLogs:
    def test_empty_sources_yields_nothing(self):
        result = list(merge_logs([]))
        assert result == []

    def test_single_source_passthrough(self):
        lines = [make_line("a", dt(1)), make_line("b", dt(2))]
        result = list(merge_logs([("src", iter(lines))]))
        assert [l.raw for l in result] == ["a", "b"]

    def test_two_sources_interleaved(self):
        a = [make_line("a1", dt(1)), make_line("a2", dt(3))]
        b = [make_line("b1", dt(2)), make_line("b2", dt(4))]
        result = list(merge_logs([("A", iter(a)), ("B", iter(b))]))
        assert [l.raw for l in result] == ["a1", "b1", "a2", "b2"]

    def test_already_sorted_sources_preserved(self):
        a = [make_line("a1", dt(1)), make_line("a2", dt(2))]
        b = [make_line("b1", dt(3)), make_line("b2", dt(4))]
        result = list(merge_logs([("A", iter(a)), ("B", iter(b))]))
        assert [l.raw for l in result] == ["a1", "a2", "b1", "b2"]

    def test_lines_without_timestamps_sort_last(self):
        a = [make_line("ts", dt(1))]
        b = [make_line("no-ts", None)]
        result = list(merge_logs([("A", iter(a)), ("B", iter(b))]))
        assert result[0].raw == "ts"
        assert result[1].raw == "no-ts"

    def test_multiple_no_timestamp_lines(self):
        a = [make_line("x", None), make_line("y", None)]
        result = list(merge_logs([("A", iter(a))]))
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Tag source option
# ---------------------------------------------------------------------------

class TestTagSource:
    def test_tag_prepended_to_raw(self):
        lines = [make_line("hello", dt(1))]
        opts = MergeOptions(tag_source=True)
        result = list(merge_logs([("app", iter(lines))], opts=opts))
        assert result[0].raw == "[app] hello"

    def test_no_tag_by_default(self):
        lines = [make_line("hello", dt(1))]
        result = list(merge_logs([("app", iter(lines))]))
        assert result[0].raw == "hello"

    def test_tag_preserves_timestamp(self):
        ts = dt(5)
        lines = [make_line("msg", ts)]
        opts = MergeOptions(tag_source=True)
        result = list(merge_logs([("svc", iter(lines))], opts=opts))
        assert result[0].timestamp == ts

    def test_three_sources_tagged(self):
        sources = [
            ("A", iter([make_line("a", dt(1))])),
            ("B", iter([make_line("b", dt(2))])),
            ("C", iter([make_line("c", dt(3))])),
        ]
        opts = MergeOptions(tag_source=True)
        result = list(merge_logs(sources, opts=opts))
        assert result[0].raw == "[A] a"
        assert result[1].raw == "[B] b"
        assert result[2].raw == "[C] c"
