"""Tests for logslice.router."""
from __future__ import annotations

import pytest
from datetime import datetime
from logslice.parser import LogLine
from logslice.router import (
    RouteRule,
    RouterOptions,
    collect_routed,
    route_lines,
)


def make_line(raw: str, level: str | None = None) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw,
    )


# ---------------------------------------------------------------------------
# RouteRule
# ---------------------------------------------------------------------------

class TestRouteRule:
    def test_matching_pattern(self):
        rule = RouteRule(channel="errors", pattern="error")
        assert rule.matches(make_line("an error occurred"))

    def test_non_matching_pattern(self):
        rule = RouteRule(channel="errors", pattern="error")
        assert not rule.matches(make_line("everything is fine"))

    def test_case_insensitive_by_default(self):
        rule = RouteRule(channel="errors", pattern="ERROR")
        assert rule.matches(make_line("an error occurred"))

    def test_case_sensitive_flag(self):
        rule = RouteRule(channel="errors", pattern="ERROR", case_sensitive=True)
        assert not rule.matches(make_line("an error occurred"))

    def test_level_match(self):
        rule = RouteRule(channel="warns", level="WARNING")
        assert rule.matches(make_line("something", level="WARNING"))

    def test_level_no_match(self):
        rule = RouteRule(channel="warns", level="WARNING")
        assert not rule.matches(make_line("something", level="ERROR"))

    def test_combined_pattern_and_level(self):
        rule = RouteRule(channel="critical", pattern="disk", level="ERROR")
        assert rule.matches(make_line("disk full", level="ERROR"))
        assert not rule.matches(make_line("disk full", level="WARNING"))
        assert not rule.matches(make_line("memory low", level="ERROR"))

    def test_empty_channel_raises(self):
        with pytest.raises(ValueError, match="channel"):
            RouteRule(channel="", pattern="x")

    def test_no_criteria_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            RouteRule(channel="ch")


# ---------------------------------------------------------------------------
# route_lines / collect_routed
# ---------------------------------------------------------------------------

class TestRouteLines:
    def _opts(self, *rules, default="default", stop=True):
        return RouterOptions(
            rules=list(rules),
            default_channel=default,
            stop_on_first_match=stop,
        )

    def test_no_rules_all_go_to_default(self):
        opts = RouterOptions()
        lines = [make_line("hello"), make_line("world")]
        result = collect_routed(lines, opts)
        assert result == {"default": lines}

    def test_matching_rule_routes_to_channel(self):
        rule = RouteRule(channel="errors", pattern="error")
        opts = self._opts(rule)
        lines = [make_line("an error"), make_line("ok")]
        result = collect_routed(lines, opts)
        assert len(result["errors"]) == 1
        assert len(result["default"]) == 1

    def test_stop_on_first_match(self):
        r1 = RouteRule(channel="a", pattern="x")
        r2 = RouteRule(channel="b", pattern="x")
        opts = self._opts(r1, r2, stop=True)
        result = collect_routed([make_line("x")], opts)
        assert "a" in result
        assert "b" not in result

    def test_no_stop_on_first_match_routes_to_multiple(self):
        r1 = RouteRule(channel="a", pattern="x")
        r2 = RouteRule(channel="b", pattern="x")
        opts = self._opts(r1, r2, stop=False)
        pairs = list(route_lines([make_line("x")], opts))
        channels = [ch for ch, _ in pairs]
        assert "a" in channels
        assert "b" in channels

    def test_enabled_reflects_rules(self):
        assert not RouterOptions().enabled()
        rule = RouteRule(channel="ch", pattern="p")
        assert RouterOptions(rules=[rule]).enabled()
