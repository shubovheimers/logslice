"""Tests for logslice.compressor."""
from __future__ import annotations

import pytest
from datetime import datetime
from logslice.parser import LogLine
from logslice.compressor import CompressOptions, compress_lines


def make_line(msg: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=f"2024-01-01 00:00:00 {level} {msg}",
        timestamp=datetime(2024, 1, 1),
        level=level,
        message=msg,
    )


def collect(lines):
    return list(compress_lines(lines))


class TestCompressOptions:
    def test_disabled_by_default(self):
        opts = CompressOptions()
        assert opts.enabled is False

    def test_min_run_default(self):
        assert CompressOptions().min_run == 3

    def test_invalid_min_run_raises(self):
        with pytest.raises(ValueError):
            CompressOptions(min_run=1)

    def test_is_active_requires_enabled(self):
        assert not CompressOptions(enabled=False).is_active()
        assert CompressOptions(enabled=True).is_active()


class TestCompressLines:
    def test_passthrough_when_disabled(self):
        lines = [make_line("hello"), make_line("hello"), make_line("hello")]
        result = collect(lines)
        assert len(result) == 3

    def test_passthrough_when_opts_none(self):
        lines = [make_line("x")] * 5
        result = list(compress_lines(lines, opts=None))
        assert len(result) == 5

    def test_run_below_min_not_compressed(self):
        opts = CompressOptions(enabled=True, min_run=3)
        lines = [make_line("same"), make_line("same")]
        result = collect(lines)
        # passthrough because opts not passed — use explicit call
        result = list(compress_lines(lines, opts=opts))
        assert len(result) == 2
        assert all("omitted" not in l.raw for l in result)

    def test_run_at_min_triggers_compression(self):
        opts = CompressOptions(enabled=True, min_run=3)
        lines = [make_line("repeat")] * 3
        result = list(compress_lines(lines, opts=opts))
        assert len(result) == 2
        assert "omitted" in result[1].raw
        assert "2" in result[1].raw  # 3 total - 1 shown = 2 omitted

    def test_long_run_reports_correct_count(self):
        opts = CompressOptions(enabled=True, min_run=3)
        lines = [make_line("flood")] * 10
        result = list(compress_lines(lines, opts=opts))
        assert len(result) == 2
        assert "9" in result[1].raw

    def test_different_messages_not_merged(self):
        opts = CompressOptions(enabled=True, min_run=2)
        lines = [make_line("a"), make_line("b"), make_line("c")]
        result = list(compress_lines(lines, opts=opts))
        assert len(result) == 3

    def test_interleaved_runs(self):
        opts = CompressOptions(enabled=True, min_run=2)
        lines = (
            [make_line("a")] * 2
            + [make_line("b")]
            + [make_line("c")] * 4
        )
        result = list(compress_lines(lines, opts=opts))
        # 'a' run → 1 line + 1 summary; 'b' → 1 line; 'c' run → 1 line + 1 summary
        assert len(result) == 5

    def test_custom_placeholder(self):
        opts = CompressOptions(enabled=True, min_run=2, placeholder="[{count} skipped]")
        lines = [make_line("dup")] * 5
        result = list(compress_lines(lines, opts=opts))
        assert "skipped" in result[1].raw
        assert "4" in result[1].raw

    def test_summary_line_has_no_level(self):
        opts = CompressOptions(enabled=True, min_run=2)
        lines = [make_line("msg")] * 3
        result = list(compress_lines(lines, opts=opts))
        assert result[1].level is None
        assert result[1].timestamp is None
