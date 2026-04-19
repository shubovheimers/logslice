"""Tests for logslice.extractor."""
from __future__ import annotations

import pytest
from datetime import datetime
from logslice.parser import LogLine
from logslice.extractor import (
    ExtractOptions,
    extract_fields,
    extract_lines,
    overwrite_ok,
)


def make_line(raw: str = "msg", level: str = "INFO", extra: dict | None = None) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw,
        extra=extra or {},
    )


class TestExtractOptions:
    def test_disabled_by_default(self):
        assert not ExtractOptions().enabled()

    def test_enabled_with_patterns(self):
        assert ExtractOptions(patterns=[r"(?P<id>\d+)"]).enabled()

    def test_none_prefix_raises(self):
        with pytest.raises((ValueError, TypeError)):
            ExtractOptions(prefix=None)  # type: ignore

    def test_invalid_pattern_raises(self):
        opts = ExtractOptions(patterns=[r"(?P<bad"])
        with pytest.raises(ValueError, match="Invalid extraction pattern"):
            opts._compile()


class TestExtractFields:
    def test_named_group_captured(self):
        import re
        pats = [re.compile(r"user=(?P<user>\w+)")]
        result = extract_fields("user=alice action=login", pats)
        assert result == {"user": "alice"}

    def test_no_match_returns_empty(self):
        import re
        pats = [re.compile(r"(?P<x>NOMATCH)")]
        assert extract_fields("hello world", pats) == {}

    def test_multiple_patterns_merged(self):
        import re
        pats = [
            re.compile(r"user=(?P<user>\w+)"),
            re.compile(r"ip=(?P<ip>[\d.]+)"),
        ]
        result = extract_fields("user=bob ip=1.2.3.4", pats)
        assert result["user"] == "bob"
        assert result["ip"] == "1.2.3.4"


class TestExtractLines:
    def test_passthrough_when_disabled(self):
        lines = [make_line("hello")]
        out = list(extract_lines(lines, ExtractOptions()))
        assert len(out) == 1
        assert out[0].raw == "hello"

    def test_passthrough_when_none(self):
        lines = [make_line("hello")]
        out = list(extract_lines(lines, None))
        assert out[0].raw == "hello"

    def test_field_added_to_extra(self):
        opts = ExtractOptions(patterns=[r"user=(?P<user>\w+)"], prefix="")
        line = make_line("user=carol")
        out = list(extract_lines([line], opts))
        assert out[0].extra["user"] == "carol"

    def test_prefix_applied(self):
        opts = ExtractOptions(patterns=[r"(?P<id>\d+)"], prefix="log_")
        line = make_line("id=42 event=start")
        out = list(extract_lines([line], opts))
        assert "log_id" in out[0].extra

    def test_no_match_line_passed_through(self):
        opts = ExtractOptions(patterns=[r"(?P<x>NOMATCH)"])
        line = make_line("nothing here")
        out = list(extract_lines([line], opts))
        assert out[0] is line

    def test_overwrite_false_keeps_existing(self):
        opts = ExtractOptions(patterns=[r"(?P<user>\w+)"], prefix="", overwrite=False)
        line = make_line("admin", extra={"user": "original"})
        out = list(extract_lines([line], opts))
        assert out[0].extra["user"] == "original"

    def test_overwrite_true_replaces_existing(self):
        opts = ExtractOptions(patterns=[r"(?P<user>\w+)"], prefix="", overwrite=True)
        line = make_line("admin", extra={"user": "original"})
        out = list(extract_lines([line], opts))
        assert out[0].extra["user"] == "admin"
