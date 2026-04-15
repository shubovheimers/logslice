"""Tests for logslice.tracer."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogLine
from logslice.tracer import (
    TraceOptions,
    extract_trace_id,
    group_by_trace,
    trace_lines,
)


def make_line(raw: str, extra: Optional[dict] = None) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level="INFO",
        message=raw,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# TraceOptions
# ---------------------------------------------------------------------------

class TestTraceOptions:
    def test_defaults_not_active(self):
        opts = TraceOptions()
        assert not opts.is_active()

    def test_enabled_with_field(self):
        opts = TraceOptions(enabled=True, field="request_id")
        assert opts.is_active()

    def test_enabled_with_pattern(self):
        opts = TraceOptions(enabled=True, pattern=r"req=(?P<trace_id>\w+)")
        assert opts.is_active()

    def test_not_active_when_enabled_but_no_field_or_pattern(self):
        opts = TraceOptions(enabled=True)
        assert not opts.is_active()


# ---------------------------------------------------------------------------
# extract_trace_id
# ---------------------------------------------------------------------------

class TestExtractTraceId:
    def test_from_extra_field(self):
        opts = TraceOptions(enabled=True, field="tid")
        line = make_line("hello", extra={"tid": "abc123"})
        assert extract_trace_id(line, opts) == "abc123"

    def test_missing_extra_field_returns_none(self):
        opts = TraceOptions(enabled=True, field="tid")
        line = make_line("hello", extra={})
        assert extract_trace_id(line, opts) is None

    def test_from_pattern(self):
        opts = TraceOptions(enabled=True, pattern=r"req=(?P<trace_id>[a-z0-9]+)")
        line = make_line("GET /api req=deadbeef status=200")
        assert extract_trace_id(line, opts) == "deadbeef"

    def test_pattern_no_match_returns_none(self):
        opts = TraceOptions(enabled=True, pattern=r"req=(?P<trace_id>[a-z0-9]+)")
        line = make_line("no trace here")
        assert extract_trace_id(line, opts) is None


# ---------------------------------------------------------------------------
# group_by_trace
# ---------------------------------------------------------------------------

def test_group_by_trace_buckets_correctly():
    opts = TraceOptions(enabled=True, field="tid")
    lines = [
        make_line("a", extra={"tid": "x1"}),
        make_line("b", extra={"tid": "x2"}),
        make_line("c", extra={"tid": "x1"}),
    ]
    buckets = group_by_trace(lines, opts)
    assert set(buckets.keys()) == {"x1", "x2"}
    assert len(buckets["x1"]) == 2
    assert len(buckets["x2"]) == 1


def test_group_by_trace_skips_lines_without_id():
    opts = TraceOptions(enabled=True, field="tid")
    lines = [make_line("no tid"), make_line("has tid", extra={"tid": "z"})]
    buckets = group_by_trace(lines, opts)
    assert list(buckets.keys()) == ["z"]


# ---------------------------------------------------------------------------
# trace_lines
# ---------------------------------------------------------------------------

def test_trace_lines_passthrough_when_not_active():
    opts = TraceOptions()
    lines = [make_line("hello")]
    assert list(trace_lines(lines, opts)) == lines


def test_trace_lines_filters_by_specific_id():
    opts = TraceOptions(enabled=True, field="tid", trace_id="wanted")
    lines = [
        make_line("a", extra={"tid": "wanted"}),
        make_line("b", extra={"tid": "other"}),
        make_line("c", extra={"tid": "wanted"}),
    ]
    result = list(trace_lines(lines, opts))
    assert len(result) == 2
    assert all(l.extra["tid"] == "wanted" for l in result)


def test_trace_lines_all_traced_when_no_id_specified():
    opts = TraceOptions(enabled=True, field="tid")
    lines = [
        make_line("a", extra={"tid": "x"}),
        make_line("b"),  # no tid — excluded
        make_line("c", extra={"tid": "y"}),
    ]
    result = list(trace_lines(lines, opts))
    assert len(result) == 2
