"""Tests for logslice.tagger."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.tagger import (
    TagRule,
    TaggerOptions,
    build_tagger_options,
    tag_lines,
)


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
        extra={},
    )


def collect(lines) -> List[LogLine]:
    return list(lines)


class TestTagRule:
    def test_matching_pattern(self):
        rule = TagRule(tag="db", pattern=r"database")
        line = make_line("database connection failed")
        assert rule.matches(line)

    def test_non_matching_pattern(self):
        rule = TagRule(tag="db", pattern=r"database")
        line = make_line("network timeout")
        assert not rule.matches(line)

    def test_case_insensitive_by_default(self):
        rule = TagRule(tag="db", pattern=r"DATABASE")
        line = make_line("database error")
        assert rule.matches(line)

    def test_case_sensitive_flag(self):
        rule = TagRule(tag="db", pattern=r"DATABASE", case_sensitive=True)
        line = make_line("database error")
        assert not rule.matches(line)


class TestTaggerOptions:
    def test_disabled_when_no_rules(self):
        opts = TaggerOptions(rules=[])
        assert not opts.enabled()

    def test_enabled_with_rules(self):
        opts = TaggerOptions(rules=[TagRule(tag="x", pattern="err")])
        assert opts.enabled()


class TestTagLines:
    def test_passthrough_when_opts_none(self):
        lines = [make_line("hello"), make_line("world")]
        result = collect(tag_lines(lines, None))
        assert result == lines

    def test_passthrough_when_no_rules(self):
        opts = TaggerOptions(rules=[])
        lines = [make_line("hello")]
        result = collect(tag_lines(lines, opts))
        assert result == lines

    def test_matching_line_gets_tag(self):
        opts = TaggerOptions(rules=[TagRule(tag="error", pattern=r"error")])
        lines = [make_line("an error occurred")]
        result = collect(tag_lines(lines, opts))
        assert result[0].extra["tags"] == ["error"]

    def test_non_matching_line_unchanged(self):
        opts = TaggerOptions(rules=[TagRule(tag="error", pattern=r"error")])
        lines = [make_line("all good")]
        result = collect(tag_lines(lines, opts))
        assert result[0].extra.get("tags") is None

    def test_multi_tags_applied(self):
        opts = TaggerOptions(rules=[
            TagRule(tag="slow", pattern=r"timeout"),
            TagRule(tag="network", pattern=r"timeout"),
        ], multi=True)
        lines = [make_line("connection timeout")]
        result = collect(tag_lines(lines, opts))
        assert "slow" in result[0].extra["tags"]
        assert "network" in result[0].extra["tags"]

    def test_single_tag_stops_at_first_match(self):
        opts = TaggerOptions(rules=[
            TagRule(tag="slow", pattern=r"timeout"),
            TagRule(tag="network", pattern=r"timeout"),
        ], multi=False)
        lines = [make_line("connection timeout")]
        result = collect(tag_lines(lines, opts))
        assert result[0].extra["tags"] == ["slow"]

    def test_existing_tags_preserved(self):
        opts = TaggerOptions(rules=[TagRule(tag="new", pattern=r"error")])
        line = make_line("error")
        line = LogLine(raw=line.raw, timestamp=line.timestamp, level=line.level,
                       message=line.message, extra={"tags": ["old"]})
        result = collect(tag_lines([line], opts))
        assert "old" in result[0].extra["tags"]
        assert "new" in result[0].extra["tags"]


class TestBuildTaggerOptions:
    def test_empty_rules(self):
        opts = build_tagger_options(rules=[])
        assert not opts.enabled()

    def test_builds_rules_from_dicts(self):
        opts = build_tagger_options(rules=[
            {"tag": "db", "pattern": "database"},
            {"tag": "net", "pattern": "network", "case_sensitive": True},
        ])
        assert len(opts.rules) == 2
        assert opts.rules[0].tag == "db"
        assert opts.rules[1].case_sensitive is True

    def test_multi_flag_passed_through(self):
        opts = build_tagger_options(rules=[], multi=False)
        assert opts.multi is False
