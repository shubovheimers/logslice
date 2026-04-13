"""Tests for logslice.formatter."""

from datetime import datetime
import pytest
from logslice.parser import LogLine
from logslice.formatter import FormatOptions, format_line, format_lines, RESET


def make_line(
    raw="2024-01-15 10:00:00 INFO  Starting service",
    level="INFO",
    message="Starting service",
    timestamp=None,
):
    ts = timestamp or datetime(2024, 1, 15, 10, 0, 0)
    return LogLine(raw=raw, timestamp=ts, level=level, message=message)


class TestFormatLineDefaults:
    def test_returns_raw_text_by_default(self):
        line = make_line()
        opts = FormatOptions()
        result = format_line(line, opts)
        assert result == line.raw.rstrip()

    def test_no_color_by_default(self):
        line = make_line()
        opts = FormatOptions()
        result = format_line(line, opts)
        assert "\033[" not in result

    def test_no_line_number_by_default(self):
        line = make_line()
        opts = FormatOptions()
        result = format_line(line, opts)
        assert not result.startswith(" ")
        assert ":" not in result.split()[0]


class TestFormatLineNumbers:
    def test_line_number_prefix(self):
        line = make_line()
        opts = FormatOptions(show_line_numbers=True)
        result = format_line(line, opts, line_number=42)
        assert result.startswith("    42:")

    def test_no_number_when_none(self):
        line = make_line()
        opts = FormatOptions(show_line_numbers=True)
        result = format_line(line, opts, line_number=None)
        assert "42" not in result


class TestFormatLineColor:
    def test_error_level_colorized(self):
        line = make_line(level="ERROR", raw="2024-01-15 10:00:00 ERROR  Crash")
        opts = FormatOptions(colorize=True)
        result = format_line(line, opts)
        assert "\033[31m" in result
        assert RESET in result

    def test_unknown_level_no_color(self):
        line = make_line(level="TRACE", raw="2024-01-15 10:00:00 TRACE  hi")
        opts = FormatOptions(colorize=True)
        result = format_line(line, opts)
        assert "\033[" not in result


class TestFormatLineFields:
    def test_selected_fields_only(self):
        line = make_line()
        opts = FormatOptions(fields=["level", "message"])
        result = format_line(line, opts)
        assert "INFO" in result
        assert "Starting service" in result
        assert "2024" not in result

    def test_custom_timestamp_format(self):
        line = make_line()
        opts = FormatOptions(fields=["timestamp"], timestamp_format="%Y/%m/%d")
        result = format_line(line, opts)
        assert "2024/01/15" in result


class TestFormatLines:
    def test_format_multiple_lines(self):
        lines = [make_line(), make_line(level="ERROR", raw="err", message="err")]
        opts = FormatOptions()
        results = format_lines(lines, opts)
        assert len(results) == 2

    def test_line_numbers_increment(self):
        lines = [make_line(), make_line()]
        opts = FormatOptions(show_line_numbers=True)
        results = format_lines(lines, opts, start_number=5)
        assert "     5:" in results[0]
        assert "     6:" in results[1]
