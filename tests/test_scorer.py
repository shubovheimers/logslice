"""Tests for logslice.scorer."""
from __future__ import annotations

import pytest
from datetime import datetime
from logslice.parser import LogLine
from logslice.scorer import (
    ScoreRule,
    ScorerOptions,
    ScoredLine,
    score_line,
    score_lines,
)


def make_line(text: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
    )


class TestScoreRule:
    def test_matching_pattern_returns_weight(self):
        rule = ScoreRule(pattern="error", weight=2.0)
        assert rule.score("an error occurred") == 2.0

    def test_no_match_returns_zero(self):
        rule = ScoreRule(pattern="critical")
        assert rule.score("everything is fine") == 0.0

    def test_multiple_matches_multiply_weight(self):
        rule = ScoreRule(pattern="fail", weight=1.5)
        assert rule.score("fail fail fail") == pytest.approx(4.5)

    def test_case_insensitive_by_default(self):
        rule = ScoreRule(pattern="ERROR")
        assert rule.score("an error happened") == 1.0

    def test_case_sensitive_no_match(self):
        rule = ScoreRule(pattern="ERROR", case_sensitive=True)
        assert rule.score("an error happened") == 0.0


class TestScorerOptions:
    def test_disabled_with_no_rules(self):
        opts = ScorerOptions()
        assert not opts.enabled()

    def test_enabled_with_rules(self):
        opts = ScorerOptions(rules=[ScoreRule(pattern="error")])
        assert opts.enabled()


class TestScoreLines:
    def test_no_rules_passthrough_all(self):
        lines = [make_line("hello"), make_line("world")]
        opts = ScorerOptions()
        result = list(score_lines(lines, opts))
        assert len(result) == 2
        assert all(sl.score == 0.0 for sl in result)

    def test_threshold_filters_low_scores(self):
        lines = [make_line("critical failure"), make_line("all good")]
        opts = ScorerOptions(
            rules=[ScoreRule(pattern="critical", weight=5.0)],
            threshold=3.0,
        )
        result = list(score_lines(lines, opts))
        assert len(result) == 1
        assert result[0].line.message == "critical failure"

    def test_results_sorted_by_score_descending(self):
        lines = [
            make_line("minor issue"),
            make_line("critical critical critical"),
            make_line("critical error"),
        ]
        opts = ScorerOptions(rules=[ScoreRule(pattern="critical", weight=1.0)])
        result = list(score_lines(lines, opts))
        scores = [sl.score for sl in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limits_results(self):
        lines = [make_line(f"error line {i}") for i in range(10)]
        opts = ScorerOptions(
            rules=[ScoreRule(pattern="error", weight=1.0)],
            top_n=3,
        )
        result = list(score_lines(lines, opts))
        assert len(result) == 3

    def test_empty_input_yields_nothing(self):
        opts = ScorerOptions(rules=[ScoreRule(pattern="error")])
        result = list(score_lines([], opts))
        assert result == []
