"""Tests for logslice.mapper."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.mapper import MapOptions, MapRule, map_lines
from logslice.parser import LogLine


def make_line(text: str, level: str = "INFO", extra=None) -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
        extra=extra or {},
    )


def collect(lines) -> List[LogLine]:
    return list(lines)


class TestMapOptions:
    def test_defaults_not_enabled(self):
        opts = MapOptions()
        assert not opts.enabled()

    def test_with_rules_enabled(self):
        opts = MapOptions(rules=[MapRule("req", r"req=(\w+)")])
        assert opts.enabled()

    def test_default_prefix(self):
        opts = MapOptions()
        assert opts.prefix == "map_"

    def test_overwrite_default_false(self):
        assert MapOptions().overwrite is False


class TestMapRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            MapRule("", r"\d+")

    def test_empty_expression_raises(self):
        with pytest.raises(ValueError):
            MapRule("field", "")

    def test_apply_with_group(self):
        rule = MapRule("id", r"id=(\d+)")
        line = make_line("request id=42 done")
        assert rule.apply(line) == "42"

    def test_apply_no_group_returns_full_match(self):
        rule = MapRule("word", r"\bERROR\b")
        line = make_line("ERROR occurred")
        assert rule.apply(line) == "ERROR"

    def test_apply_no_match_returns_none(self):
        rule = MapRule("id", r"id=(\d+)")
        line = make_line("no match here")
        assert rule.apply(line) is None


class TestMapLines:
    def test_passthrough_when_no_opts(self):
        lines = [make_line("hello")]
        result = collect(map_lines(lines, None))
        assert result == lines

    def test_passthrough_when_disabled(self):
        lines = [make_line("hello")]
        result = collect(map_lines(lines, MapOptions()))
        assert result == lines

    def test_field_extracted_with_prefix(self):
        opts = MapOptions(rules=[MapRule("code", r"code=(\d+)")])
        line = make_line("exit code=99 done")
        result = collect(map_lines([line], opts))
        assert result[0].extra.get("map_code") == "99"

    def test_no_match_field_absent(self):
        opts = MapOptions(rules=[MapRule("code", r"code=(\d+)")])
        line = make_line("no code here")
        result = collect(map_lines([line], opts))
        assert "map_code" not in result[0].extra

    def test_overwrite_false_keeps_existing(self):
        opts = MapOptions(rules=[MapRule("code", r"code=(\d+)")], overwrite=False)
        line = make_line("exit code=99", extra={"map_code": "old"})
        result = collect(map_lines([line], opts))
        assert result[0].extra["map_code"] == "old"

    def test_overwrite_true_replaces_existing(self):
        opts = MapOptions(rules=[MapRule("code", r"code=(\d+)")], overwrite=True)
        line = make_line("exit code=99", extra={"map_code": "old"})
        result = collect(map_lines([line], opts))
        assert result[0].extra["map_code"] == "99"

    def test_custom_prefix(self):
        opts = MapOptions(rules=[MapRule("user", r"user=(\w+)")], prefix="x_")
        line = make_line("user=alice login")
        result = collect(map_lines([line], opts))
        assert result[0].extra.get("x_user") == "alice"

    def test_multiple_rules(self):
        opts = MapOptions(rules=[
            MapRule("user", r"user=(\w+)"),
            MapRule("code", r"code=(\d+)"),
        ])
        line = make_line("user=bob code=200")
        result = collect(map_lines([line], opts))
        assert result[0].extra["map_user"] == "bob"
        assert result[0].extra["map_code"] == "200"
