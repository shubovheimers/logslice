"""Tests for logslice.classifier."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.classifier import (
    ClassifyOptions,
    ClassifyRule,
    classify_line,
    classify_lines,
    group_by_category,
)
from logslice.parser import LogLine


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
    )


# ---------------------------------------------------------------------------
# ClassifyRule
# ---------------------------------------------------------------------------

class TestClassifyRule:
    def test_matching_pattern(self):
        rule = ClassifyRule(name="db", pattern=r"database")
        assert rule.matches("database connection failed") is True

    def test_non_matching_pattern(self):
        rule = ClassifyRule(name="db", pattern=r"database")
        assert rule.matches("network timeout") is False

    def test_case_insensitive(self):
        rule = ClassifyRule(name="err", pattern=r"error")
        assert rule.matches("ERROR: something went wrong") is True


# ---------------------------------------------------------------------------
# ClassifyOptions
# ---------------------------------------------------------------------------

class TestClassifyOptions:
    def test_enabled_with_rules(self):
        opts = ClassifyOptions(rules=[ClassifyRule("x", "x")])
        assert opts.enabled is True

    def test_not_enabled_without_rules(self):
        opts = ClassifyOptions()
        assert opts.enabled is False


# ---------------------------------------------------------------------------
# classify_line
# ---------------------------------------------------------------------------

class TestClassifyLine:
    def test_first_matching_rule_wins(self):
        opts = ClassifyOptions(rules=[
            ClassifyRule("auth", r"login|logout"),
            ClassifyRule("error", r"error"),
        ])
        line = make_line("user login error")
        _, cat = classify_line(line, opts)
        assert cat == "auth"

    def test_default_when_no_rule_matches(self):
        opts = ClassifyOptions(
            rules=[ClassifyRule("db", r"database")],
            default_category="other",
        )
        _, cat = classify_line(make_line("network timeout"), opts)
        assert cat == "other"


# ---------------------------------------------------------------------------
# classify_lines
# ---------------------------------------------------------------------------

class TestClassifyLines:
    def test_none_opts_yields_default(self):
        lines = [make_line("hello"), make_line("world")]
        results = list(classify_lines(lines, None))
        assert all(cat == "uncategorised" for _, cat in results)
        assert len(results) == 2

    def test_disabled_opts_yields_default(self):
        opts = ClassifyOptions(default_category="misc")
        results = list(classify_lines([make_line("x")], opts))
        assert results[0][1] == "misc"

    def test_classifies_correctly(self):
        opts = ClassifyOptions(rules=[ClassifyRule("db", r"sql")])
        lines = [make_line("sql query"), make_line("http request")]
        cats = [cat for _, cat in classify_lines(lines, opts)]
        assert cats == ["db", "uncategorised"]


# ---------------------------------------------------------------------------
# group_by_category
# ---------------------------------------------------------------------------

class TestGroupByCategory:
    def test_groups_correctly(self):
        opts = ClassifyOptions(rules=[
            ClassifyRule("auth", r"login"),
            ClassifyRule("db", r"sql"),
        ])
        lines = [
            make_line("user login"),
            make_line("sql select"),
            make_line("user login again"),
            make_line("unknown event"),
        ]
        groups = group_by_category(lines, opts)
        assert len(groups["auth"]) == 2
        assert len(groups["db"]) == 1
        assert len(groups["uncategorised"]) == 1

    def test_empty_input_returns_empty_dict(self):
        opts = ClassifyOptions(rules=[ClassifyRule("x", "x")])
        assert group_by_category([], opts) == {}
