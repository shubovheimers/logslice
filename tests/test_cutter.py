"""Tests for logslice.cutter."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.cutter import CutOptions, cut_line, cut_lines


def make_line(raw: str, extra=None) -> LogLine:
    return LogLine(raw=raw, timestamp=None, level=None, message=raw, extra=extra or {})


# ---------------------------------------------------------------------------
# CutOptions validation
# ---------------------------------------------------------------------------

class TestCutOptions:
    def test_defaults_not_active(self):
        assert not CutOptions().is_active()

    def test_enabled_without_delimiter_or_pattern_not_active(self):
        assert not CutOptions(enabled=True).is_active()

    def test_delimiter_enables(self):
        assert CutOptions(enabled=True, delimiter="|").is_active()

    def test_pattern_enables(self):
        assert CutOptions(enabled=True, pattern=r"(?P<ip>\S+)").is_active()

    def test_both_raises(self):
        with pytest.raises(ValueError):
            CutOptions(enabled=True, delimiter="|", pattern=r"(?P<x>\d+)")

    def test_invalid_regex_raises(self):
        with pytest.raises(re.error if False else Exception):
            CutOptions(enabled=True, pattern=r"(?P<unclosed")


import re  # noqa: E402 (needed for the test above)


# ---------------------------------------------------------------------------
# cut_line – delimiter mode
# ---------------------------------------------------------------------------

class TestCutLineDelimiter:
    def test_splits_into_named_fields(self):
        line = make_line("alice|30|admin")
        opts = CutOptions(enabled=True, delimiter="|", fields=["user", "age", "role"])
        result = cut_line(line, opts)
        assert result.extra["user"] == "alice"
        assert result.extra["age"] == "30"
        assert result.extra["role"] == "admin"

    def test_unnamed_columns_get_auto_names(self):
        line = make_line("a|b|c")
        opts = CutOptions(enabled=True, delimiter="|", fields=["first"])
        result = cut_line(line, opts)
        assert result.extra["first"] == "a"
        assert result.extra["field1"] == "b"
        assert result.extra["field2"] == "c"

    def test_inactive_opts_returns_unchanged(self):
        line = make_line("a|b")
        opts = CutOptions(enabled=False, delimiter="|")
        assert cut_line(line, opts) is line


# ---------------------------------------------------------------------------
# cut_line – pattern mode
# ---------------------------------------------------------------------------

class TestCutLinePattern:
    def test_named_groups_extracted(self):
        line = make_line("2024-01-15 ERROR Something failed")
        opts = CutOptions(
            enabled=True,
            pattern=r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<level>\w+) (?P<msg>.*)",
        )
        result = cut_line(line, opts)
        assert result.extra["date"] == "2024-01-15"
        assert result.extra["level"] == "ERROR"
        assert result.extra["msg"] == "Something failed"

    def test_no_match_returns_empty_extra(self):
        line = make_line("no match here")
        opts = CutOptions(enabled=True, pattern=r"(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
        result = cut_line(line, opts)
        assert result.extra == {}

    def test_existing_extra_preserved(self):
        line = make_line("hello world", extra={"src": "file.log"})
        opts = CutOptions(enabled=True, pattern=r"(?P<word>\w+)")
        result = cut_line(line, opts)
        assert result.extra["src"] == "file.log"
        assert "word" in result.extra


# ---------------------------------------------------------------------------
# cut_lines iterator
# ---------------------------------------------------------------------------

def test_cut_lines_yields_all():
    lines = [make_line(f"val{i}|{i}") for i in range(4)]
    opts = CutOptions(enabled=True, delimiter="|", fields=["name", "idx"])
    results = list(cut_lines(lines, opts))
    assert len(results) == 4
    assert results[2].extra["idx"] == "2"
