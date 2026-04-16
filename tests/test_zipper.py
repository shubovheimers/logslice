"""Tests for logslice.zipper."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.zipper import ZipOptions, zip_logs


def make_line(msg: str, ts: datetime | None = None, level: str | None = None) -> LogLine:
    return LogLine(raw=msg, timestamp=ts, level=level, message=msg, extra={})


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute)


def collect(a, b, opts=None) -> List[LogLine]:
    return list(zip_logs(a, b, opts))


class TestZipOptions:
    def test_defaults(self):
        o = ZipOptions()
        assert o.fill_missing is False
        assert o.tag_a == "A"
        assert o.tag_b == "B"
        assert o.strict_order is True
        assert o.enabled()

    def test_custom_tags(self):
        o = ZipOptions(tag_a="app", tag_b="svc")
        assert o.tag_a == "app"
        assert o.tag_b == "svc"


class TestZipLogs:
    def test_empty_both_yields_nothing(self):
        assert collect([], []) == []

    def test_single_a_only(self):
        lines = collect([make_line("a1")], [])
        assert len(lines) == 1
        assert lines[0].extra["_zip_source"] == "A"

    def test_single_b_only(self):
        lines = collect([], [make_line("b1")])
        assert len(lines) == 1
        assert lines[0].extra["_zip_source"] == "B"

    def test_tags_applied(self):
        a = [make_line("a", dt(1))]
        b = [make_line("b", dt(2))]
        result = collect(a, b)
        assert result[0].extra["_zip_source"] == "A"
        assert result[1].extra["_zip_source"] == "B"

    def test_strict_order_by_timestamp(self):
        a = [make_line("a1", dt(1)), make_line("a2", dt(3))]
        b = [make_line("b1", dt(2)), make_line("b2", dt(4))]
        result = collect(a, b)
        messages = [r.message for r in result]
        assert messages == ["a1", "b1", "a2", "b2"]

    def test_no_timestamp_sorts_last(self):
        a = [make_line("a_no_ts", None)]
        b = [make_line("b_ts", dt(1))]
        result = collect(a, b)
        assert result[0].message == "b_ts"
        assert result[1].message == "a_no_ts"

    def test_fill_missing_inserts_placeholder(self):
        opts = ZipOptions(fill_missing=True, fill_text="---")
        a = [make_line("a1", dt(1)), make_line("a2", dt(2))]
        b = [make_line("b1", dt(1))]
        result = collect(a, b, opts)
        sources = [r.extra["_zip_source"] for r in result]
        # placeholder for B should appear when B is exhausted
        assert "B" in sources

    def test_custom_tags_propagated(self):
        opts = ZipOptions(tag_a="left", tag_b="right")
        a = [make_line("l", dt(1))]
        b = [make_line("r", dt(2))]
        result = collect(a, b, opts)
        assert result[0].extra["_zip_source"] == "left"
        assert result[1].extra["_zip_source"] == "right"

    def test_original_extra_preserved(self):
        line = LogLine(raw="x", timestamp=dt(1), level="INFO", message="x",
                       extra={"foo": "bar"})
        result = collect([line], [])
        assert result[0].extra["foo"] == "bar"
        assert result[0].extra["_zip_source"] == "A"
