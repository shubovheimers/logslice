"""Tests for logslice.dropper."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.dropper import DropOptions, drop_lines


def make_line(raw: str, level: str | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=datetime(2024, 1, 1), level=level, message=raw, extra={})


def collect(lines) -> List[str]:
    return [ln.raw for ln in lines]


class TestDropOptions:
    def test_defaults_not_active(self):
        opts = DropOptions()
        assert not opts.is_active()

    def test_pattern_activates(self):
        opts = DropOptions(patterns=["error"])
        assert opts.is_active()

    def test_level_activates(self):
        opts = DropOptions(levels=["DEBUG"])
        assert opts.is_active()

    def test_should_drop_matching_pattern(self):
        opts = DropOptions(patterns=[r"secret"])
        assert opts.should_drop(make_line("contains secret data"))

    def test_should_not_drop_non_matching(self):
        opts = DropOptions(patterns=[r"secret"])
        assert not opts.should_drop(make_line("safe line"))

    def test_should_drop_matching_level(self):
        opts = DropOptions(levels=["debug"])
        assert opts.should_drop(make_line("msg", level="DEBUG"))

    def test_level_case_insensitive(self):
        opts = DropOptions(levels=["DEBUG"])
        assert opts.should_drop(make_line("msg", level="debug"))

    def test_case_sensitive_pattern(self):
        opts = DropOptions(patterns=["Error"], case_sensitive=True)
        assert not opts.should_drop(make_line("error in system"))
        assert opts.should_drop(make_line("Error in system"))


class TestDropLines:
    def test_none_opts_passthrough(self):
        lines = [make_line("a"), make_line("b")]
        assert collect(drop_lines(lines, None)) == ["a", "b"]

    def test_inactive_opts_passthrough(self):
        lines = [make_line("a"), make_line("b")]
        assert collect(drop_lines(lines, DropOptions())) == ["a", "b"]

    def test_drops_matching_pattern(self):
        lines = [make_line("keep this"), make_line("drop secret now"), make_line("also keep")]
        opts = DropOptions(patterns=["secret"])
        assert collect(drop_lines(lines, opts)) == ["keep this", "also keep"]

    def test_drops_matching_level(self):
        lines = [
            make_line("debug msg", level="DEBUG"),
            make_line("info msg", level="INFO"),
            make_line("debug2", level="DEBUG"),
        ]
        opts = DropOptions(levels=["debug"])
        assert collect(drop_lines(lines, opts)) == ["info msg"]

    def test_drops_by_pattern_and_level(self):
        lines = [
            make_line("normal", level="INFO"),
            make_line("verbose trace", level="DEBUG"),
            make_line("has password=xyz", level="INFO"),
        ]
        opts = DropOptions(patterns=["password"], levels=["DEBUG"])
        result = collect(drop_lines(lines, opts))
        assert result == ["normal"]

    def test_empty_input_yields_nothing(self):
        opts = DropOptions(patterns=["x"])
        assert collect(drop_lines([], opts)) == []
