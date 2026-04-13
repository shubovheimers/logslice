"""Tests for logslice.stats module."""

import datetime
from collections import Counter

import pytest

from logslice.parser import LogLine
from logslice.stats import LogStats, collect_stats, format_stats


def make_line(
    raw="2024-01-01T10:00:00 INFO hello",
    timestamp=None,
    level="INFO",
    message="hello",
) -> LogLine:
    ts = timestamp or datetime.datetime(2024, 1, 1, 10, 0, 0)
    return LogLine(raw=raw, timestamp=ts, level=level, message=message)


class TestLogStats:
    def test_time_span_with_both_timestamps(self):
        stats = LogStats(
            first_timestamp=datetime.datetime(2024, 1, 1, 10, 0, 0),
            last_timestamp=datetime.datetime(2024, 1, 1, 11, 0, 0),
        )
        assert stats.time_span == datetime.timedelta(hours=1)

    def test_time_span_missing_timestamps(self):
        stats = LogStats()
        assert stats.time_span is None

    def test_as_dict_keys(self):
        stats = LogStats(total_lines=10, matched_lines=5)
        d = stats.as_dict()
        assert "total_lines" in d
        assert "matched_lines" in d
        assert "level_counts" in d
        assert "time_span_seconds" in d


class TestCollectStats:
    def test_counts_matched_lines(self):
        lines = [make_line() for _ in range(5)]
        stats = collect_stats(lines, total_lines=10)
        assert stats.matched_lines == 5
        assert stats.total_lines == 10

    def test_level_counts(self):
        lines = [
            make_line(level="INFO"),
            make_line(level="ERROR"),
            make_line(level="INFO"),
        ]
        stats = collect_stats(lines)
        assert stats.level_counts["INFO"] == 2
        assert stats.level_counts["ERROR"] == 1

    def test_level_normalised_to_upper(self):
        lines = [make_line(level="debug")]
        stats = collect_stats(lines)
        assert "DEBUG" in stats.level_counts

    def test_skipped_when_no_level(self):
        lines = [make_line(level=None)]
        stats = collect_stats(lines)
        assert stats.skipped_lines == 1

    def test_first_and_last_timestamp(self):
        t1 = datetime.datetime(2024, 1, 1, 9, 0, 0)
        t2 = datetime.datetime(2024, 1, 1, 11, 0, 0)
        lines = [make_line(timestamp=t1), make_line(timestamp=t2)]
        stats = collect_stats(lines)
        assert stats.first_timestamp == t1
        assert stats.last_timestamp == t2

    def test_empty_iterable(self):
        stats = collect_stats([], total_lines=100)
        assert stats.matched_lines == 0
        assert stats.total_lines == 100
        assert stats.first_timestamp is None


class TestFormatStats:
    def test_contains_totals(self):
        stats = LogStats(total_lines=50, matched_lines=20)
        output = format_stats(stats)
        assert "50" in output
        assert "20" in output

    def test_contains_level_summary(self):
        stats = LogStats(level_counts=Counter({"ERROR": 3, "INFO": 7}))
        output = format_stats(stats)
        assert "ERROR=3" in output
        assert "INFO=7" in output

    def test_no_timestamp_section_when_missing(self):
        stats = LogStats()
        output = format_stats(stats)
        assert "First timestamp" not in output

    def test_time_span_shown(self):
        stats = LogStats(
            first_timestamp=datetime.datetime(2024, 1, 1, 8, 0, 0),
            last_timestamp=datetime.datetime(2024, 1, 1, 10, 0, 0),
        )
        output = format_stats(stats)
        assert "Time span" in output
