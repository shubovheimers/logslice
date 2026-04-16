"""Tests for logslice.pivotter."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.pivotter import (
    PivotOptions,
    format_pivot,
    pivot_lines,
)


def make_line(level: str = "INFO", source: str = "app", raw: str = "", extra: dict | None = None) -> LogLine:
    return LogLine(
        raw=raw or f"{level} message",
        timestamp=None,
        level=level,
        source=source,
        message=raw or f"{level} message",
        extra=extra or {},
    )


class TestPivotOptions:
    def test_defaults(self):
        opts = PivotOptions()
        assert opts.by == "level"
        assert opts.top_n == 0
        assert opts.min_count == 1

    def test_negative_top_n_raises(self):
        with pytest.raises(ValueError):
            PivotOptions(top_n=-1)

    def test_zero_min_count_raises(self):
        with pytest.raises(ValueError):
            PivotOptions(min_count=0)

    def test_enabled(self):
        assert PivotOptions(by="level").enabled()
        assert PivotOptions(pattern=r"(?P<key>\w+)").enabled()


class TestPivotLines:
    def _lines(self):
        return [
            make_line("INFO"),
            make_line("INFO"),
            make_line("ERROR"),
            make_line("WARN"),
            make_line("ERROR"),
            make_line("ERROR"),
        ]

    def test_by_level_counts(self):
        table = pivot_lines(self._lines(), PivotOptions(by="level"))
        assert table["ERROR"] == 3
        assert table["INFO"] == 2
        assert table["WARN"] == 1

    def test_top_n_limits(self):
        table = pivot_lines(self._lines(), PivotOptions(by="level", top_n=2))
        assert len(table) == 2
        assert "ERROR" in table
        assert "INFO" in table

    def test_min_count_filters(self):
        table = pivot_lines(self._lines(), PivotOptions(by="level", min_count=2))
        assert "WARN" not in table
        assert "INFO" in table
        assert "ERROR" in table

    def test_by_source(self):
        lines = [make_line(source="web"), make_line(source="db"), make_line(source="web")]
        table = pivot_lines(lines, PivotOptions(by="source"))
        assert table["web"] == 2
        assert table["db"] == 1

    def test_pattern_extraction(self):
        lines = [
            make_line(raw="request_id=abc123 done"),
            make_line(raw="request_id=abc123 retry"),
            make_line(raw="request_id=xyz999 done"),
        ]
        opts = PivotOptions(pattern=r"request_id=(?P<key>\w+)")
        table = pivot_lines(lines, opts)
        assert table["abc123"] == 2
        assert table["xyz999"] == 1

    def test_empty_input(self):
        table = pivot_lines([], PivotOptions())
        assert table == {}


class TestFormatPivot:
    def test_no_results(self):
        rows = list(format_pivot({}))
        assert rows == ["(no results)"]

    def test_rows_contain_key_and_count(self):
        rows = list(format_pivot({"INFO": 5, "ERROR": 2}, total=7))
        assert any("INFO" in r and "5" in r for r in rows)
        assert any("ERROR" in r and "2" in r for r in rows)

    def test_sorted_by_count_descending(self):
        rows = list(format_pivot({"INFO": 5, "ERROR": 10}))
        assert rows[0].startswith("ERROR")
