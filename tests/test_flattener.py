"""Tests for logslice.flattener and logslice.cli_flattener."""
from __future__ import annotations

import argparse
from datetime import datetime
from typing import List

import pytest

from logslice.flattener import FlattenOptions, flatten_lines
from logslice.cli_flattener import add_flatten_args, flatten_opts_from_args
from logslice.parser import LogLine


def make_line(raw: str, message: str = "") -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level="INFO",
        message=message or raw,
        extra={},
    )


def collect(lines) -> List[LogLine]:
    return list(flatten_lines(lines, opts=None))


# ---------------------------------------------------------------------------
# FlattenOptions
# ---------------------------------------------------------------------------

class TestFlattenOptions:
    def test_disabled_by_default(self):
        opts = FlattenOptions()
        assert opts.enabled is False

    def test_default_separator(self):
        opts = FlattenOptions()
        assert opts.join_separator == " "

    def test_default_max_continuation(self):
        opts = FlattenOptions()
        assert opts.max_continuation == 50

    def test_invalid_max_continuation_raises(self):
        with pytest.raises(ValueError):
            FlattenOptions(max_continuation=0)

    def test_is_record_start_matches(self):
        opts = FlattenOptions(record_start_pattern=r"^\d{4}-")
        assert opts.is_record_start("2024-01-01 INFO hello")

    def test_is_record_start_no_match(self):
        opts = FlattenOptions(record_start_pattern=r"^\d{4}-")
        assert not opts.is_record_start("    at com.example.Foo")


# ---------------------------------------------------------------------------
# flatten_lines — passthrough cases
# ---------------------------------------------------------------------------

class TestFlattenPassthrough:
    def test_none_opts_yields_unchanged(self):
        lines = [make_line("2024-01-01 hello"), make_line("    stack")]
        result = list(flatten_lines(lines, opts=None))
        assert result == lines

    def test_disabled_opts_yields_unchanged(self):
        opts = FlattenOptions(enabled=False)
        lines = [make_line("2024-01-01 hello"), make_line("    stack")]
        result = list(flatten_lines(lines, opts=opts))
        assert result == lines

    def test_empty_input_yields_nothing(self):
        opts = FlattenOptions(enabled=True)
        assert list(flatten_lines([], opts=opts)) == []


# ---------------------------------------------------------------------------
# flatten_lines — merging behaviour
# ---------------------------------------------------------------------------

class TestFlattenMerge:
    def _opts(self, **kw) -> FlattenOptions:
        return FlattenOptions(enabled=True, record_start_pattern=r"^\d{4}-", **kw)

    def test_single_record_no_continuation(self):
        opts = self._opts()
        lines = [make_line("2024-01-01 INFO hello", "hello")]
        result = list(flatten_lines(lines, opts=opts))
        assert len(result) == 1
        assert result[0].message == "hello"

    def test_continuation_merged_into_preceding(self):
        opts = self._opts(join_separator=" | ")
        lines = [
            make_line("2024-01-01 INFO error", "error"),
            make_line("    at Foo.bar", "at Foo.bar"),
        ]
        result = list(flatten_lines(lines, opts=opts))
        assert len(result) == 1
        assert "at Foo.bar" in result[0].message

    def test_two_records_separated_correctly(self):
        opts = self._opts()
        lines = [
            make_line("2024-01-01 first", "first"),
            make_line("    cont", "cont"),
            make_line("2024-01-02 second", "second"),
        ]
        result = list(flatten_lines(lines, opts=opts))
        assert len(result) == 2
        assert "cont" in result[0].message
        assert result[1].message == "second"

    def test_max_continuation_cap_flushes(self):
        opts = self._opts(max_continuation=2)
        lines = [
            make_line("2024-01-01 start", "start"),
            make_line("    line1", "line1"),
            make_line("    line2", "line2"),
            make_line("    line3", "line3"),  # exceeds cap
        ]
        result = list(flatten_lines(lines, opts=opts))
        # After cap is hit the overflow line starts a new record
        assert len(result) == 2

    def test_orphan_continuation_emitted_as_is(self):
        opts = self._opts()
        lines = [make_line("    no start yet", "no start yet")]
        result = list(flatten_lines(lines, opts=opts))
        assert len(result) == 1
        assert result[0].message == "no start yet"


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_flatten_args(p)
    return p


class TestAddFlattenArgs:
    def test_flatten_flag_defaults_false(self):
        args = _make_parser().parse_args([])
        assert args.flatten is False

    def test_flatten_flag_true_when_set(self):
        args = _make_parser().parse_args(["--flatten"])
        assert args.flatten is True

    def test_default_pattern(self):
        args = _make_parser().parse_args([])
        assert "\\d{4}" in args.flatten_pattern

    def test_custom_pattern(self):
        args = _make_parser().parse_args(["--flatten-pattern", r"^\["]) 
        assert args.flatten_pattern == r"^\["

    def test_default_separator(self):
        args = _make_parser().parse_args([])
        assert args.flatten_separator == " "

    def test_custom_max_continuation(self):
        args = _make_parser().parse_args(["--flatten-max-continuation", "10"])
        assert args.flatten_max_continuation == 10


class TestFlattenOptsFromArgs:
    def test_disabled_by_default(self):
        args = _make_parser().parse_args([])
        opts = flatten_opts_from_args(args)
        assert opts.enabled is False

    def test_enabled_when_flag_set(self):
        args = _make_parser().parse_args(["--flatten"])
        opts = flatten_opts_from_args(args)
        assert opts.enabled is True

    def test_separator_propagated(self):
        args = _make_parser().parse_args(["--flatten-separator", "\\n"])
        opts = flatten_opts_from_args(args)
        assert opts.join_separator == "\\n"
