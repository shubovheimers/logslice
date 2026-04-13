"""Tests for logslice.summarizer."""
from __future__ import annotations

from collections import Counter
from datetime import datetime

import pytest

from logslice.parser import LogLine
from logslice.summarizer import (
    LogSummary,
    SummaryOptions,
    format_summary,
    summarize_lines,
)


def make_line(raw: str, level: str | None = None, ts: datetime | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw)


DT1 = datetime(2024, 1, 1, 10, 0, 0)
DT2 = datetime(2024, 1, 1, 11, 0, 0)
DT3 = datetime(2024, 1, 1, 12, 0, 0)


class TestSummarizeLines:
    def test_empty_input_returns_zero_total(self):
        s = summarize_lines([])
        assert s.total_lines == 0

    def test_counts_all_lines(self):
        lines = [make_line("a"), make_line("b"), make_line("c")]
        s = summarize_lines(lines)
        assert s.total_lines == 3

    def test_first_and_last_timestamp(self):
        lines = [
            make_line("a", ts=DT1),
            make_line("b", ts=DT2),
            make_line("c", ts=DT3),
        ]
        s = summarize_lines(lines)
        assert s.first_timestamp == DT1
        assert s.last_timestamp == DT3

    def test_no_timestamps_leaves_none(self):
        lines = [make_line("a"), make_line("b")]
        s = summarize_lines(lines)
        assert s.first_timestamp is None
        assert s.last_timestamp is None

    def test_level_counts(self):
        lines = [
            make_line("a", level="INFO"),
            make_line("b", level="ERROR"),
            make_line("c", level="info"),
        ]
        s = summarize_lines(lines)
        assert s.level_counts["INFO"] == 2
        assert s.level_counts["ERROR"] == 1

    def test_level_counting_disabled(self):
        opts = SummaryOptions(count_levels=False)
        lines = [make_line("a", level="INFO")]
        s = summarize_lines(lines, opts)
        assert len(s.level_counts) == 0

    def test_top_messages_respects_top_n(self):
        opts = SummaryOptions(top_n=2)
        lines = [make_line("x") for _ in range(5)] + [make_line("y") for _ in range(3)]
        s = summarize_lines(lines, opts)
        assert len(s.top_messages) == 2
        assert s.top_messages[0][0] == "x"
        assert s.top_messages[0][1] == 5

    def test_pattern_counting_disabled(self):
        opts = SummaryOptions(count_patterns=False)
        lines = [make_line("msg") for _ in range(3)]
        s = summarize_lines(lines, opts)
        assert s.top_messages == []

    def test_time_range_returns_tuple(self):
        lines = [make_line("a", ts=DT1), make_line("b", ts=DT3)]
        s = summarize_lines(lines)
        assert s.time_range() == (DT1, DT3)

    def test_time_range_none_when_no_timestamps(self):
        s = LogSummary()
        assert s.time_range() is None


class TestFormatSummary:
    def test_contains_total_lines(self):
        s = LogSummary(total_lines=42)
        out = format_summary(s)
        assert "42" in out

    def test_contains_level_info(self):
        s = LogSummary(total_lines=2, level_counts=Counter({"ERROR": 2}))
        out = format_summary(s)
        assert "ERROR" in out
        assert "2" in out

    def test_contains_top_messages(self):
        s = LogSummary(total_lines=3, top_messages=[("disk full", 3)])
        out = format_summary(s)
        assert "disk full" in out

    def test_time_range_shown_when_present(self):
        s = LogSummary(total_lines=1, first_timestamp=DT1, last_timestamp=DT3)
        out = format_summary(s)
        assert "First entry" in out
        assert "Last entry" in out

    def test_no_time_range_section_when_absent(self):
        s = LogSummary(total_lines=0)
        out = format_summary(s)
        assert "First entry" not in out
