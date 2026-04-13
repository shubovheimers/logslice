"""Tests for logslice.highlighter."""

from __future__ import annotations

import pytest

from logslice.highlighter import (
    LEVEL_COLORS,
    PATTERN_COLOR,
    RESET,
    BOLD,
    HighlightOptions,
    apply_highlighting,
    colorize_level,
    highlight_pattern,
)


class TestColorizeLevel:
    def test_known_level_adds_color(self):
        result = colorize_level("ERROR something broke", "ERROR")
        assert LEVEL_COLORS["ERROR"] in result
        assert RESET in result

    def test_unknown_level_unchanged(self):
        text = "TRACE some message"
        assert colorize_level(text, "TRACE") == text

    def test_none_level_unchanged(self):
        text = "plain text"
        assert colorize_level(text, None) == text

    def test_warning_alias(self):
        result = colorize_level("WARN low disk", "WARN")
        assert LEVEL_COLORS["WARN"] in result

    def test_bold_applied(self):
        result = colorize_level("INFO startup", "INFO")
        assert BOLD in result


class TestHighlightPattern:
    def test_simple_word_highlighted(self):
        result = highlight_pattern("connection timeout occurred", "timeout")
        assert PATTERN_COLOR in result
        assert "timeout" in result
        assert RESET in result

    def test_regex_pattern(self):
        result = highlight_pattern("id=42 value=99", r"id=\d+")
        assert PATTERN_COLOR in result

    def test_invalid_regex_returns_original(self):
        text = "some log line"
        result = highlight_pattern(text, "[invalid")
        assert result == text

    def test_no_match_returns_original(self):
        text = "nothing here"
        result = highlight_pattern(text, "xyz")
        assert result == text


class TestApplyHighlighting:
    def test_level_colorized_when_enabled(self):
        opts = HighlightOptions(colorize_levels=True)
        result = apply_highlighting("ERROR bad thing", "ERROR", opts)
        assert LEVEL_COLORS["ERROR"] in result

    def test_level_not_colorized_when_disabled(self):
        opts = HighlightOptions(colorize_levels=False)
        result = apply_highlighting("ERROR bad thing", "ERROR", opts)
        assert LEVEL_COLORS["ERROR"] not in result

    def test_pattern_highlighted(self):
        opts = HighlightOptions(highlight_patterns=["bad"])
        result = apply_highlighting("ERROR bad thing", "ERROR", opts)
        assert PATTERN_COLOR in result

    def test_multiple_patterns(self):
        opts = HighlightOptions(
            colorize_levels=False,
            highlight_patterns=["bad", "thing"],
        )
        result = apply_highlighting("bad thing happened", None, opts)
        assert result.count(PATTERN_COLOR) == 2

    def test_no_options_returns_plain(self):
        opts = HighlightOptions(colorize_levels=False)
        text = "INFO plain message"
        assert apply_highlighting(text, "INFO", opts) == text
