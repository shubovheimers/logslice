"""Tests for logslice.selector."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.selector import SelectRule, SelectorOptions, select_lines


def make_line(text: str = "msg", **extra) -> LogLine:
    return LogLine(raw=text, text=text, level=None, timestamp=None, extra=extra)


# ---------------------------------------------------------------------------
# SelectRule
# ---------------------------------------------------------------------------

class TestSelectRule:
    def test_matching_pattern(self):
        rule = SelectRule(key="service", pattern="auth")
        line = make_line(service="auth-service")
        assert rule.matches(line) is True

    def test_non_matching_pattern(self):
        rule = SelectRule(key="service", pattern="^db$")
        line = make_line(service="auth-service")
        assert rule.matches(line) is False

    def test_missing_key_returns_false(self):
        rule = SelectRule(key="host", pattern=".*")
        line = make_line(service="auth")
        assert rule.matches(line) is False

    def test_case_insensitive_by_default(self):
        rule = SelectRule(key="env", pattern="PROD")
        line = make_line(env="prod")
        assert rule.matches(line) is True

    def test_case_sensitive_flag(self):
        rule = SelectRule(key="env", pattern="PROD", case_sensitive=True)
        line = make_line(env="prod")
        assert rule.matches(line) is False


# ---------------------------------------------------------------------------
# SelectorOptions
# ---------------------------------------------------------------------------

class TestSelectorOptions:
    def test_disabled_when_no_rules(self):
        opts = SelectorOptions()
        assert opts.enabled() is False

    def test_enabled_with_rules(self):
        opts = SelectorOptions(rules=[SelectRule(key="k", pattern="v")])
        assert opts.enabled() is True

    def test_require_all_default_true(self):
        opts = SelectorOptions()
        assert opts.require_all is True


# ---------------------------------------------------------------------------
# select_lines
# ---------------------------------------------------------------------------

def collect(lines):
    return list(select_lines(lines, None))


class TestSelectLines:
    def test_passthrough_when_opts_none(self):
        lines = [make_line("a"), make_line("b")]
        assert list(select_lines(lines, None)) == lines

    def test_passthrough_when_disabled(self):
        opts = SelectorOptions(rules=[])
        lines = [make_line("a")]
        assert list(select_lines(lines, opts)) == lines

    def test_and_semantics_both_match(self):
        opts = SelectorOptions(
            rules=[
                SelectRule(key="env", pattern="prod"),
                SelectRule(key="service", pattern="auth"),
            ],
            require_all=True,
        )
        line = make_line(env="prod", service="auth-svc")
        result = list(select_lines([line], opts))
        assert result == [line]

    def test_and_semantics_one_fails(self):
        opts = SelectorOptions(
            rules=[
                SelectRule(key="env", pattern="prod"),
                SelectRule(key="service", pattern="^db$"),
            ],
            require_all=True,
        )
        line = make_line(env="prod", service="auth-svc")
        assert list(select_lines([line], opts)) == []

    def test_or_semantics_one_matches(self):
        opts = SelectorOptions(
            rules=[
                SelectRule(key="env", pattern="prod"),
                SelectRule(key="service", pattern="^db$"),
            ],
            require_all=False,
        )
        line = make_line(env="prod", service="auth-svc")
        result = list(select_lines([line], opts))
        assert result == [line]

    def test_or_semantics_none_matches(self):
        opts = SelectorOptions(
            rules=[
                SelectRule(key="env", pattern="staging"),
                SelectRule(key="service", pattern="^db$"),
            ],
            require_all=False,
        )
        line = make_line(env="prod", service="auth-svc")
        assert list(select_lines([line], opts)) == []

    def test_filters_mixed_lines(self):
        opts = SelectorOptions(
            rules=[SelectRule(key="level", pattern="error")]
        )
        lines = [
            make_line("e1", level="error"),
            make_line("i1", level="info"),
            make_line("e2", level="ERROR"),
        ]
        result = list(select_lines(lines, opts))
        assert len(result) == 2
        assert result[0].text == "e1"
        assert result[1].text == "e2"
