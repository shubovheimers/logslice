"""Tests for the log line parser module."""

from datetime import datetime

import pytest

from logslice.parser import LogLine, parse_line, parse_timestamp


class TestParseTimestamp:
    def test_iso8601_basic(self):
        result = parse_timestamp("2024-01-15T13:45:00")
        assert result == datetime(2024, 1, 15, 13, 45, 0)

    def test_iso8601_with_microseconds(self):
        result = parse_timestamp("2024-01-15T13:45:00.123456")
        assert result == datetime(2024, 1, 15, 13, 45, 0, 123456)

    def test_iso8601_with_timezone_stripped(self):
        result = parse_timestamp("2024-01-15T13:45:00Z")
        assert result == datetime(2024, 1, 15, 13, 45, 0)

    def test_space_separated_datetime(self):
        result = parse_timestamp("2024-01-15 13:45:00")
        assert result == datetime(2024, 1, 15, 13, 45, 0)

    def test_syslog_format(self):
        result = parse_timestamp("Jan 15 13:45:00")
        assert result is not None
        assert result.month == 1 and result.day == 15

    def test_invalid_returns_none(self):
        assert parse_timestamp("not-a-date") is None


class TestParseLine:
    def test_iso_timestamp_extracted(self):
        line = "2024-03-10T08:22:01 INFO Application started"
        result = parse_line(line)
        assert result.timestamp == datetime(2024, 3, 10, 8, 22, 1)

    def test_log_level_extracted(self):
        line = "2024-03-10T08:22:01 ERROR Something went wrong"
        result = parse_line(line)
        assert result.level == "ERROR"

    def test_log_level_case_insensitive(self):
        line = "2024-03-10T08:22:01 warning low disk space"
        result = parse_line(line)
        assert result.level == "WARNING"

    def test_no_timestamp_returns_none(self):
        line = "INFO No timestamp here"
        result = parse_line(line)
        assert result.timestamp is None

    def test_no_level_returns_none(self):
        line = "2024-03-10T08:22:01 some message without level"
        result = parse_line(line)
        assert result.level is None

    def test_raw_preserved(self):
        line = "2024-03-10T08:22:01 DEBUG raw line content"
        result = parse_line(line)
        assert result.raw == line

    def test_returns_logline_instance(self):
        result = parse_line("some log line")
        assert isinstance(result, LogLine)

    def test_newline_stripped_from_raw(self):
        line = "2024-03-10T08:22:01 INFO test\n"
        result = parse_line(line)
        assert not result.raw.endswith("\n")
