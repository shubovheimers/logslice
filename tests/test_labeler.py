"""Tests for logslice.labeler."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.labeler import LabelRule, LabelerOptions, label_lines
from logslice.parser import LogLine


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(raw=text, timestamp=datetime(2024, 1, 1), level=level, message=text, extra={})


def collect(lines) -> List[LogLine]:
    return list(lines)


class TestLabelerOptions:
    def test_disabled_by_default(self):
        opts = LabelerOptions()
        assert not opts.enabled()

    def test_enabled_with_rules(self):
        opts = LabelerOptions(rules=[LabelRule(pattern="error", label="is_error")])
        assert opts.enabled()

    def test_enabled_with_static_labels(self):
        opts = LabelerOptions(static_labels={"env": "prod"})
        assert opts.enabled()


class TestLabelLines:
    def test_passthrough_when_none(self):
        lines = [make_line("hello")]
        result = collect(label_lines(lines, None))
        assert result == lines

    def test_passthrough_when_disabled(self):
        lines = [make_line("hello")]
        result = collect(label_lines(lines, LabelerOptions()))
        assert result == lines

    def test_static_label_applied_to_all(self):
        opts = LabelerOptions(static_labels={"env": "staging"})
        lines = [make_line("msg1"), make_line("msg2")]
        result = collect(label_lines(lines, opts))
        assert all(r.extra["env"] == "staging" for r in result)

    def test_pattern_rule_matches(self):
        rule = LabelRule(pattern="timeout", label="is_timeout")
        opts = LabelerOptions(rules=[rule])
        lines = [make_line("connection timeout"), make_line("all good")]
        result = collect(label_lines(lines, opts))
        assert result[0].extra.get("is_timeout") == "true"
        assert "is_timeout" not in result[1].extra

    def test_pattern_rule_case_insensitive_by_default(self):
        rule = LabelRule(pattern="ERROR", label="flagged")
        opts = LabelerOptions(rules=[rule])
        result = collect(label_lines([make_line("error occurred")], opts))
        assert result[0].extra.get("flagged") == "true"

    def test_pattern_rule_case_sensitive(self):
        rule = LabelRule(pattern="ERROR", label="flagged", case_sensitive=True)
        opts = LabelerOptions(rules=[rule])
        result = collect(label_lines([make_line("error occurred")], opts))
        assert "flagged" not in result[0].extra

    def test_custom_value(self):
        rule = LabelRule(pattern="warn", label="severity", value="warning")
        opts = LabelerOptions(rules=[rule])
        result = collect(label_lines([make_line("warn: disk low")], opts))
        assert result[0].extra["severity"] == "warning"

    def test_static_and_pattern_combined(self):
        rule = LabelRule(pattern="fail", label="failed")
        opts = LabelerOptions(rules=[rule], static_labels={"host": "web1"})
        lines = [make_line("task failed"), make_line("task ok")]
        result = collect(label_lines(lines, opts))
        assert result[0].extra["host"] == "web1"
        assert result[0].extra["failed"] == "true"
        assert result[1].extra["host"] == "web1"
        assert "failed" not in result[1].extra

    def test_original_extra_preserved(self):
        line = LogLine(raw="msg", timestamp=None, level=None, message="msg", extra={"existing": "val"})
        opts = LabelerOptions(static_labels={"new": "x"})
        result = collect(label_lines([line], opts))
        assert result[0].extra["existing"] == "val"
        assert result[0].extra["new"] == "x"
