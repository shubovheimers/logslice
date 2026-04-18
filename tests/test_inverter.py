"""Tests for logslice.inverter."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.inverter import InvertOptions, invert_lines
from logslice.parser import LogLine


def make_line(raw: str, level: str | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=datetime(2024, 1, 1), level=level, message=raw)


def collect(lines) -> List[str]:
    return [ln.raw for ln in lines]


class TestInvertOptions:
    def test_disabled_by_default(self):
        opts = InvertOptions()
        assert not opts.enabled

    def test_enabled_with_pattern(self):
        opts = InvertOptions(patterns=["error"])
        assert opts.enabled

    def test_enabled_with_level(self):
        opts = InvertOptions(invert_level="DEBUG")
        assert opts.enabled

    def test_level_normalised_to_upper(self):
        opts = InvertOptions(invert_level="debug")
        assert opts.invert_level == "DEBUG"


class TestInvertLines:
    def test_passthrough_when_disabled(self):
        lines = [make_line("hello"), make_line("world")]
        result = collect(invert_lines(lines, None))
        assert result == ["hello", "world"]

    def test_passthrough_when_no_patterns_no_level(self):
        opts = InvertOptions()
        lines = [make_line("hello"), make_line("world")]
        result = collect(invert_lines(lines, opts))
        assert result == ["hello", "world"]

    def test_excludes_matching_pattern(self):
        opts = InvertOptions(patterns=["error"])
        lines = [make_line("an error occurred"), make_line("all good")]
        result = collect(invert_lines(lines, opts))
        assert result == ["all good"]

    def test_case_insensitive_by_default(self):
        opts = InvertOptions(patterns=["ERROR"])
        lines = [make_line("an error occurred"), make_line("all good")]
        result = collect(invert_lines(lines, opts))
        assert result == ["all good"]

    def test_case_sensitive_no_match(self):
        opts = InvertOptions(patterns=["ERROR"], case_sensitive=True)
        lines = [make_line("an error occurred"), make_line("all good")]
        # lowercase 'error' does NOT match uppercase pattern when case_sensitive
        result = collect(invert_lines(lines, opts))
        assert result == ["an error occurred", "all good"]

    def test_excludes_by_level(self):
        opts = InvertOptions(invert_level="DEBUG")
        lines = [
            make_line("debug msg", level="DEBUG"),
            make_line("info msg", level="INFO"),
        ]
        result = collect(invert_lines(lines, opts))
        assert result == ["info msg"]

    def test_multiple_patterns_any_match_excludes(self):
        opts = InvertOptions(patterns=["foo", "bar"])
        lines = [make_line("foo here"), make_line("bar here"), make_line("baz here")]
        result = collect(invert_lines(lines, opts))
        assert result == ["baz here"]

    def test_empty_input_yields_nothing(self):
        opts = InvertOptions(patterns=["error"])
        result = collect(invert_lines([], opts))
        assert result == []
