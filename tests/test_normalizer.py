"""Tests for logslice.normalizer."""

from __future__ import annotations

import pytest

from logslice.normalizer import (
    NormalizeOptions,
    apply_normalization,
    collapse_whitespace,
    normalize_line,
    normalize_text,
    strip_ansi,
)
from logslice.parser import LogLine


def make_line(raw: str, message: str = "") -> LogLine:
    return LogLine(raw=raw, timestamp=None, level=None, message=message, extra={})


# ---------------------------------------------------------------------------
# strip_ansi
# ---------------------------------------------------------------------------

class TestStripAnsi:
    def test_removes_color_codes(self):
        assert strip_ansi("\x1b[31mERROR\x1b[0m") == "ERROR"

    def test_plain_text_unchanged(self):
        assert strip_ansi("hello world") == "hello world"

    def test_multiple_sequences(self):
        assert strip_ansi("\x1b[1m\x1b[32mOK\x1b[0m") == "OK"


# ---------------------------------------------------------------------------
# collapse_whitespace
# ---------------------------------------------------------------------------

class TestCollapseWhitespace:
    def test_multiple_spaces_collapsed(self):
        assert collapse_whitespace("foo   bar") == "foo bar"

    def test_tabs_collapsed(self):
        assert collapse_whitespace("foo\t\tbar") == "foo bar"

    def test_leading_trailing_stripped(self):
        assert collapse_whitespace("  hello  ") == "hello"


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_strip_ansi_enabled(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=True)
        assert normalize_text("\x1b[31mERR\x1b[0m", opts) == "ERR"

    def test_max_line_length_truncates(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=False, max_line_length=5)
        assert normalize_text("hello world", opts) == "hello"

    def test_zero_max_length_no_truncation(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=False, max_line_length=0)
        assert normalize_text("hello world", opts) == "hello world"

    def test_unicode_normalization_nfc(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=False, unicode_normalize="NFC")
        # precomposed e-acute
        result = normalize_text("\u00e9", opts)
        assert result == "\u00e9"


# ---------------------------------------------------------------------------
# normalize_line
# ---------------------------------------------------------------------------

class TestNormalizeLine:
    def test_raw_text_normalized(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=True)
        line = make_line(raw="\x1b[32mINFO\x1b[0m msg")
        result = normalize_line(line, opts)
        assert result.raw == "INFO msg"

    def test_message_normalized(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=True)
        line = make_line(raw="raw", message="\x1b[31merr\x1b[0m")
        result = normalize_line(line, opts)
        assert result.message == "err"

    def test_timestamp_preserved(self):
        from datetime import datetime
        opts = NormalizeOptions(enabled=True)
        ts = datetime(2024, 1, 1, 12, 0, 0)
        line = LogLine(raw="text", timestamp=ts, level="INFO", message="m", extra={})
        result = normalize_line(line, opts)
        assert result.timestamp == ts


# ---------------------------------------------------------------------------
# apply_normalization
# ---------------------------------------------------------------------------

class TestApplyNormalization:
    def test_passthrough_when_disabled(self):
        opts = NormalizeOptions(enabled=False)
        lines = [make_line("\x1b[31mERR\x1b[0m")]
        result = list(apply_normalization(lines, opts))
        assert result[0].raw == "\x1b[31mERR\x1b[0m"

    def test_passthrough_when_none(self):
        lines = [make_line("\x1b[31mERR\x1b[0m")]
        result = list(apply_normalization(lines, None))
        assert result[0].raw == "\x1b[31mERR\x1b[0m"

    def test_applies_when_enabled(self):
        opts = NormalizeOptions(enabled=True, strip_ansi=True)
        lines = [make_line("\x1b[31mERR\x1b[0m"), make_line("\x1b[32mOK\x1b[0m")]
        result = list(apply_normalization(lines, opts))
        assert result[0].raw == "ERR"
        assert result[1].raw == "OK"
