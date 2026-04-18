"""Tests for logslice.trimmer."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.trimmer import TrimOptions, trim_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=None, level=None, message=text, extra={})


def collect(lines, opts):
    return list(trim_lines(lines, opts))


class TestTrimOptions:
    def test_disabled_by_default(self):
        opts = TrimOptions()
        assert opts.enabled is False

    def test_not_active_when_disabled(self):
        opts = TrimOptions(enabled=False)
        assert not opts.is_active()

    def test_active_when_enabled(self):
        opts = TrimOptions(enabled=True)
        assert opts.is_active()

    def test_negative_max_consecutive_raises(self):
        with pytest.raises(ValueError):
            TrimOptions(max_consecutive_blanks=-1)

    def test_not_active_when_both_strips_false(self):
        opts = TrimOptions(enabled=True, strip_blank_lines=False, strip_inline_whitespace=False)
        assert not opts.is_active()


class TestTrimLinesPassthrough:
    def test_passthrough_when_opts_none(self):
        lines = [make_line("hello"), make_line("world")]
        assert collect(lines, None) == lines

    def test_passthrough_when_disabled(self):
        lines = [make_line("  hello  "), make_line("")]
        opts = TrimOptions(enabled=False)
        result = collect(lines, opts)
        assert [l.raw for l in result] == ["  hello  ", ""]


class TestStripInlineWhitespace:
    def test_strips_leading_trailing_spaces(self):
        opts = TrimOptions(enabled=True, strip_blank_lines=False)
        lines = [make_line("  hello  "), make_line("world")]
        result = collect(lines, opts)
        assert result[0].raw == "hello"
        assert result[1].raw == "world"

    def test_plain_line_unchanged(self):
        opts = TrimOptions(enabled=True)
        lines = [make_line("no extra spaces")]
        result = collect(lines, opts)
        assert result[0].raw == "no extra spaces"


class TestStripBlankLines:
    def test_removes_blank_lines_by_default(self):
        opts = TrimOptions(enabled=True, max_consecutive_blanks=0)
        lines = [make_line("a"), make_line(""), make_line("b")]
        result = collect(lines, opts)
        assert [l.raw for l in result] == ["a", "b"]

    def test_allows_one_consecutive_blank(self):
        opts = TrimOptions(enabled=True, max_consecutive_blanks=1)
        lines = [make_line("a"), make_line(""), make_line(""), make_line("b")]
        result = collect(lines, opts)
        assert [l.raw for l in result] == ["a", "", "b"]

    def test_trailing_blanks_not_emitted(self):
        opts = TrimOptions(enabled=True, max_consecutive_blanks=1)
        lines = [make_line("a"), make_line(""), make_line("")]
        result = collect(lines, opts)
        assert [l.raw for l in result] == ["a"]
