"""Tests for logslice.alerter."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import pytest

from logslice.alerter import (
    AlertFired,
    AlertOptions,
    AlertRule,
    evaluate_alerts,
)
from logslice.parser import LogLine


def make_line(
    raw: str,
    level: Optional[str] = None,
    ts: Optional[datetime] = None,
) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw)


def dt(second: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, second)


# ---------------------------------------------------------------------------
# AlertRule.matches
# ---------------------------------------------------------------------------

class TestAlertRuleMatches:
    def test_matching_pattern(self):
        rule = AlertRule(name="r", pattern="error")
        assert rule.matches(make_line("an ERROR occurred"))

    def test_non_matching_pattern(self):
        rule = AlertRule(name="r", pattern="error")
        assert not rule.matches(make_line("everything is fine"))

    def test_level_filter_passes(self):
        rule = AlertRule(name="r", pattern="fail", level="ERROR")
        assert rule.matches(make_line("fail hard", level="ERROR"))

    def test_level_filter_blocks(self):
        rule = AlertRule(name="r", pattern="fail", level="ERROR")
        assert not rule.matches(make_line("fail hard", level="INFO"))

    def test_no_level_filter_ignores_level(self):
        rule = AlertRule(name="r", pattern="ok")
        assert rule.matches(make_line("ok", level="DEBUG"))


# ---------------------------------------------------------------------------
# AlertOptions
# ---------------------------------------------------------------------------

class TestAlertOptions:
    def test_enabled_when_rules_provided(self):
        opts = AlertOptions(rules=[AlertRule(name="r", pattern="x")])
        assert opts.enabled

    def test_disabled_when_no_rules(self):
        opts = AlertOptions()
        assert not opts.enabled


# ---------------------------------------------------------------------------
# evaluate_alerts
# ---------------------------------------------------------------------------

class TestEvaluateAlerts:
    def _run(self, lines, rules) -> List[AlertFired]:
        opts = AlertOptions(rules=rules)
        return list(evaluate_alerts(lines, opts))

    def test_no_rules_yields_nothing(self):
        lines = [make_line("error", ts=dt(1))]
        result = list(evaluate_alerts(lines, AlertOptions()))
        assert result == []

    def test_single_match_at_threshold_1(self):
        rule = AlertRule(name="err", pattern="error", threshold=1, window_seconds=60)
        lines = [make_line("error here", ts=dt(1))]
        result = self._run(lines, [rule])
        assert len(result) == 1
        assert result[0].rule_name == "err"

    def test_below_threshold_no_alert(self):
        rule = AlertRule(name="err", pattern="error", threshold=3, window_seconds=60)
        lines = [make_line("error", ts=dt(i)) for i in range(2)]
        assert self._run(lines, [rule]) == []

    def test_fires_once_not_repeatedly(self):
        rule = AlertRule(name="err", pattern="error", threshold=1, window_seconds=60)
        lines = [make_line("error", ts=dt(i)) for i in range(5)]
        result = self._run(lines, [rule])
        assert len(result) == 1

    def test_alert_fired_str_contains_name(self):
        rule = AlertRule(name="myalert", pattern="boom", threshold=1)
        lines = [make_line("boom", ts=dt(0))]
        result = self._run(lines, [rule])
        assert "myalert" in str(result[0])

    def test_lines_without_timestamps_still_match(self):
        rule = AlertRule(name="r", pattern="critical", threshold=2, window_seconds=60)
        lines = [make_line("critical", ts=None) for _ in range(3)]
        result = self._run(lines, [rule])
        assert len(result) == 1
