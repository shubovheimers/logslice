"""Tests for logslice.squasher."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.squasher import SquashOptions, squash_lines


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw_text=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
        extra={},
    )


def collect(lines, opts):
    return list(squash_lines(lines, opts))


class TestSquashOptions:
    def test_defaults_not_active(self):
        assert not SquashOptions().is_active()

    def test_enabled_activates(self):
        assert SquashOptions(enabled=True, by_level=True).is_active()

    def test_invalid_max_group_raises(self):
        with pytest.raises(ValueError):
            SquashOptions(max_group=0)


class TestSquashLines:
    def test_passthrough_when_disabled(self):
        opts = SquashOptions(enabled=False)
        lines = [make_line("a"), make_line("b")]
        assert collect(lines, opts) == lines

    def test_passthrough_when_opts_none(self):
        lines = [make_line("a"), make_line("b")]
        assert collect(lines, None) == lines

    def test_single_line_unchanged(self):
        opts = SquashOptions(enabled=True)
        lines = [make_line("only")]
        result = collect(lines, opts)
        assert len(result) == 1
        assert result[0].raw_text == "only"

    def test_merges_consecutive_same_level(self):
        opts = SquashOptions(enabled=True, separator=" | ")
        lines = [make_line("a", "ERROR"), make_line("b", "ERROR")]
        result = collect(lines, opts)
        assert len(result) == 1
        assert "a" in result[0].raw_text
        assert "b" in result[0].raw_text

    def test_different_levels_not_merged(self):
        opts = SquashOptions(enabled=True)
        lines = [make_line("a", "INFO"), make_line("b", "ERROR")]
        result = collect(lines, opts)
        assert len(result) == 2

    def test_max_group_respected(self):
        opts = SquashOptions(enabled=True, max_group=2)
        lines = [make_line(str(i), "WARN") for i in range(5)]
        result = collect(lines, opts)
        # groups: [0,1], [2,3], [4]
        assert len(result) == 3

    def test_separator_used_in_message(self):
        opts = SquashOptions(enabled=True, separator="##")
        lines = [make_line("x", "DEBUG"), make_line("y", "DEBUG")]
        result = collect(lines, opts)
        assert "##" in result[0].message

    def test_first_timestamp_preserved(self):
        opts = SquashOptions(enabled=True)
        t1 = datetime(2024, 1, 1, 10, 0, 0)
        t2 = datetime(2024, 1, 1, 11, 0, 0)
        l1 = LogLine(raw_text="a", timestamp=t1, level="INFO", message="a", extra={})
        l2 = LogLine(raw_text="b", timestamp=t2, level="INFO", message="b", extra={})
        result = collect([l1, l2], opts)
        assert result[0].timestamp == t1
