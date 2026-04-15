"""Integration tests for the router: rules + real LogLine data."""
from __future__ import annotations

from datetime import datetime
from logslice.parser import LogLine
from logslice.router import RouteRule, RouterOptions, collect_routed, route_lines


def _line(raw: str, level: str | None = None) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 6, 1, 10, 0, 0),
        level=level,
        message=raw,
    )


class TestRouterIntegration:
    def _make_lines(self):
        return [
            _line("disk full", level="ERROR"),
            _line("connection timeout", level="WARNING"),
            _line("user logged in", level="INFO"),
            _line("null pointer error", level="ERROR"),
            _line("cache miss", level="DEBUG"),
        ]

    def test_level_routing_separates_errors(self):
        rules = [RouteRule(channel="errors", level="ERROR")]
        opts = RouterOptions(rules=rules)
        result = collect_routed(self._make_lines(), opts)
        assert len(result["errors"]) == 2
        assert len(result["default"]) == 3

    def test_pattern_routing_matches_keyword(self):
        rules = [RouteRule(channel="disk", pattern="disk")]
        opts = RouterOptions(rules=rules)
        result = collect_routed(self._make_lines(), opts)
        assert len(result["disk"]) == 1
        assert result["disk"][0].raw == "disk full"

    def test_multiple_rules_first_wins(self):
        rules = [
            RouteRule(channel="errors", level="ERROR"),
            RouteRule(channel="disk_errors", pattern="disk"),
        ]
        opts = RouterOptions(rules=rules, stop_on_first_match=True)
        result = collect_routed(self._make_lines(), opts)
        # "disk full" is ERROR so goes to "errors", not "disk_errors"
        assert any(l.raw == "disk full" for l in result.get("errors", []))
        assert "disk_errors" not in result

    def test_multiple_rules_no_stop(self):
        rules = [
            RouteRule(channel="errors", level="ERROR"),
            RouteRule(channel="disk_errors", pattern="disk"),
        ]
        opts = RouterOptions(rules=rules, stop_on_first_match=False)
        pairs = list(route_lines(self._make_lines(), opts))
        channels = [ch for ch, ln in pairs if ln.raw == "disk full"]
        assert "errors" in channels
        assert "disk_errors" in channels

    def test_unmatched_lines_go_to_custom_default(self):
        rules = [RouteRule(channel="errors", level="ERROR")]
        opts = RouterOptions(rules=rules, default_channel="other")
        result = collect_routed(self._make_lines(), opts)
        assert "other" in result
        assert "default" not in result
        assert len(result["other"]) == 3
