"""Tests for logslice.joiner."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.joiner import JoinOptions, join_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_line(raw: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw.strip(),
        extra={},
    )


def collect(lines, opts=None) -> List[LogLine]:
    return list(join_lines(lines, opts))


# ---------------------------------------------------------------------------
# JoinOptions
# ---------------------------------------------------------------------------

class TestJoinOptions:
    def test_disabled_by_default_is_false(self):
        # enabled defaults to True
        opts = JoinOptions()
        assert opts.enabled is True

    def test_can_disable(self):
        opts = JoinOptions(enabled=False)
        assert opts.enabled is False

    def test_is_continuation_indented(self):
        opts = JoinOptions()
        assert opts.is_continuation("    at com.example.Foo.bar(Foo.java:42)")

    def test_is_continuation_caused_by(self):
        opts = JoinOptions()
        assert opts.is_continuation("Caused by: java.lang.NullPointerException")

    def test_is_not_continuation_normal_line(self):
        opts = JoinOptions()
        assert not opts.is_continuation("2024-01-01 INFO something happened")

    def test_custom_pattern(self):
        opts = JoinOptions(continuation_pattern=r"^>")
        assert opts.is_continuation("> continued")
        assert not opts.is_continuation("normal line")


# ---------------------------------------------------------------------------
# join_lines
# ---------------------------------------------------------------------------

class TestJoinLines:
    def test_passthrough_when_disabled(self):
        opts = JoinOptions(enabled=False)
        lines = [make_line("line one"), make_line("  indented")]
        result = collect(lines, opts)
        assert len(result) == 2

    def test_passthrough_when_opts_none(self):
        lines = [make_line("line one"), make_line("  indented")]
        result = collect(lines, None)
        assert len(result) == 2

    def test_single_line_passthrough(self):
        lines = [make_line("only line")]
        result = collect(lines)
        assert len(result) == 1
        assert result[0].raw == "only line"

    def test_continuation_folded_into_anchor(self):
        opts = JoinOptions(separator=" | ")
        lines = [
            make_line("ERROR something broke"),
            make_line("    at com.example.A.b(A.java:10)"),
        ]
        result = collect(lines, opts)
        assert len(result) == 1
        assert "at com.example.A.b" in result[0].raw
        assert " | " in result[0].raw

    def test_anchor_timestamp_preserved(self):
        opts = JoinOptions()
        anchor = make_line("ERROR top")
        cont = make_line("    at foo.Bar")
        result = collect([anchor, cont], opts)
        assert result[0].timestamp == anchor.timestamp

    def test_anchor_level_preserved(self):
        opts = JoinOptions()
        anchor = make_line("ERROR top", level="ERROR")
        cont = make_line("    at foo.Bar", level="ERROR")
        result = collect([anchor, cont], opts)
        assert result[0].level == "ERROR"

    def test_multiple_continuations(self):
        opts = JoinOptions()
        lines = [
            make_line("ERROR boom"),
            make_line("    at A"),
            make_line("    at B"),
            make_line("    at C"),
        ]
        result = collect(lines, opts)
        assert len(result) == 1
        assert "at A" in result[0].raw
        assert "at C" in result[0].raw

    def test_new_anchor_resets_after_non_continuation(self):
        opts = JoinOptions()
        lines = [
            make_line("ERROR first"),
            make_line("    at A"),
            make_line("INFO second event"),
            make_line("    at B"),
        ]
        result = collect(lines, opts)
        assert len(result) == 2
        assert "first" in result[0].raw
        assert "second" in result[1].raw

    def test_max_continuation_respected(self):
        opts = JoinOptions(max_continuation=2)
        lines = [make_line("ERROR anchor")] + [
            make_line(f"    at frame{i}") for i in range(5)
        ]
        result = collect(lines, opts)
        # After 2 continuations the 3rd becomes a new anchor
        assert len(result) > 1

    def test_empty_input_yields_nothing(self):
        result = collect([], JoinOptions())
        assert result == []
