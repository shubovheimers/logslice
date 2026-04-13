"""Tests for logslice.filter module."""

import pytest
from datetime import datetime
from typing import List

from logslice.parser import LogLine
from logslice.filter import (
    filter_by_time,
    filter_by_level,
    filter_by_pattern,
    apply_filters,
)


def make_line(raw: str, timestamp=None, level=None) -> LogLine:
    return LogLine(raw=raw, timestamp=timestamp, level=level, message=raw)


DT = lambda h, m: datetime(2024, 1, 15, h, m, 0)  # noqa: E731

SAMPLE_LINES: List[LogLine] = [
    make_line("DEBUG msg", DT(10, 0), "DEBUG"),
    make_line("INFO msg", DT(10, 30), "INFO"),
    make_line("WARNING msg", DT(11, 0), "WARNING"),
    make_line("ERROR msg", DT(11, 30), "ERROR"),
    make_line("no timestamp", None, "INFO"),
]


class TestFilterByTime:
    def test_start_only(self):
        result = list(filter_by_time(iter(SAMPLE_LINES), start=DT(10, 30)))
        assert len(result) == 3
        assert result[0].level == "INFO"

    def test_end_only(self):
        result = list(filter_by_time(iter(SAMPLE_LINES), end=DT(10, 30)))
        assert len(result) == 2

    def test_start_and_end(self):
        result = list(filter_by_time(iter(SAMPLE_LINES), start=DT(10, 30), end=DT(11, 0)))
        assert len(result) == 2
        assert result[0].level == "INFO"
        assert result[1].level == "WARNING"

    def test_skips_lines_without_timestamp(self):
        result = list(filter_by_time(iter(SAMPLE_LINES), start=DT(9, 0)))
        # line with None timestamp is excluded
        assert all(line.timestamp is not None for line in result)


class TestFilterByLevel:
    def test_min_info(self):
        result = list(filter_by_level(iter(SAMPLE_LINES), "INFO"))
        levels = [r.level for r in result]
        assert "DEBUG" not in levels
        assert "INFO" in levels
        assert "ERROR" in levels

    def test_min_error(self):
        result = list(filter_by_level(iter(SAMPLE_LINES), "ERROR"))
        assert len(result) == 1
        assert result[0].level == "ERROR"

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="Unknown log level"):
            list(filter_by_level(iter(SAMPLE_LINES), "VERBOSE"))

    def test_skips_lines_without_level(self):
        result = list(filter_by_level(iter(SAMPLE_LINES), "DEBUG"))
        assert all(r.level is not None for r in result)


class TestFilterByPattern:
    def test_simple_match(self):
        result = list(filter_by_pattern(iter(SAMPLE_LINES), "error"))
        assert len(result) == 1
        assert result[0].level == "ERROR"

    def test_case_insensitive_by_default(self):
        result = list(filter_by_pattern(iter(SAMPLE_LINES), "WARNING"))
        assert len(result) == 1

    def test_no_match_returns_empty(self):
        result = list(filter_by_pattern(iter(SAMPLE_LINES), "CRITICAL"))
        assert result == []


class TestApplyFilters:
    def test_combined_time_and_level(self):
        result = list(apply_filters(
            iter(SAMPLE_LINES),
            start=DT(10, 30),
            min_level="WARNING",
        ))
        assert len(result) == 2
        assert {r.level for r in result} == {"WARNING", "ERROR"}

    def test_no_filters_returns_all(self):
        result = list(apply_filters(iter(SAMPLE_LINES)))
        assert len(result) == len(SAMPLE_LINES)
