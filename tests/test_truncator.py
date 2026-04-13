"""Tests for logslice.truncator."""

import pytest
from logslice.parser import LogLine
from logslice.truncator import (
    TruncateOptions,
    truncate_text,
    truncate_line,
    apply_truncation,
)


def make_line(raw: str) -> LogLine:
    return LogLine(raw=raw, timestamp=None, level=None, message=raw, extra={})


# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------

class TestTruncateText:
    def test_disabled_returns_unchanged(self):
        opts = TruncateOptions(enabled=False, max_width=10)
        assert truncate_text("hello world", opts) == "hello world"

    def test_short_text_unchanged(self):
        opts = TruncateOptions(enabled=True, max_width=20)
        assert truncate_text("short", opts) == "short"

    def test_exact_width_unchanged(self):
        opts = TruncateOptions(enabled=True, max_width=5)
        assert truncate_text("hello", opts) == "hello"

    def test_truncate_from_end(self):
        opts = TruncateOptions(enabled=True, max_width=8, truncate_from="end")
        result = truncate_text("hello world", opts)
        assert result == "hello..."
        assert len(result) == 8

    def test_truncate_from_start(self):
        opts = TruncateOptions(enabled=True, max_width=8, truncate_from="start")
        result = truncate_text("hello world", opts)
        assert result == "...world"
        assert len(result) == 8

    def test_max_width_smaller_than_ellipsis(self):
        opts = TruncateOptions(enabled=True, max_width=2, ellipsis="...")
        result = truncate_text("hello world", opts)
        assert len(result) <= 3  # ellipsis itself clipped

    def test_custom_ellipsis(self):
        opts = TruncateOptions(enabled=True, max_width=7, ellipsis="~", truncate_from="end")
        result = truncate_text("hello world", opts)
        assert result == "hello w~"
        assert len(result) == 8  # 7 chars + 1 ellipsis


# ---------------------------------------------------------------------------
# truncate_line
# ---------------------------------------------------------------------------

class TestTruncateLine:
    def test_none_opts_returns_same_line(self):
        line = make_line("2024-01-01 INFO something happened")
        result = truncate_line(line, None)
        assert result is line

    def test_disabled_opts_returns_same_line(self):
        line = make_line("2024-01-01 INFO something happened")
        opts = TruncateOptions(enabled=False)
        result = truncate_line(line, opts)
        assert result is line

    def test_truncates_raw_text(self):
        line = make_line("2024-01-01 INFO a very long message that should be cut")
        opts = TruncateOptions(enabled=True, max_width=20)
        result = truncate_line(line, opts)
        assert len(result.raw) == 20

    def test_preserves_timestamp_and_level(self):
        from datetime import datetime
        line = LogLine(
            raw="2024-01-01 ERROR something",
            timestamp=datetime(2024, 1, 1),
            level="ERROR",
            message="something",
            extra={},
        )
        opts = TruncateOptions(enabled=True, max_width=15)
        result = truncate_line(line, opts)
        assert result.timestamp == line.timestamp
        assert result.level == line.level


# ---------------------------------------------------------------------------
# apply_truncation
# ---------------------------------------------------------------------------

class TestApplyTruncation:
    def test_none_opts_passthrough(self):
        lines = [make_line("a" * 50), make_line("b" * 50)]
        result = list(apply_truncation(lines, None))
        assert result == lines

    def test_disabled_passthrough(self):
        opts = TruncateOptions(enabled=False)
        lines = [make_line("a" * 50)]
        result = list(apply_truncation(lines, opts))
        assert result == lines

    def test_truncates_all_lines(self):
        opts = TruncateOptions(enabled=True, max_width=10)
        lines = [make_line("x" * 30) for _ in range(5)]
        result = list(apply_truncation(lines, opts))
        assert all(len(r.raw) == 10 for r in result)

    def test_empty_input(self):
        opts = TruncateOptions(enabled=True, max_width=10)
        assert list(apply_truncation([], opts)) == []
