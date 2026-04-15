"""Tests for logslice.cli_scorer."""
from __future__ import annotations

import argparse
import pytest

from logslice.cli_scorer import add_scorer_args, scorer_opts_from_args, _parse_rule
from logslice.scorer import ScoreRule, ScorerOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_scorer_args(p)
    return p


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(score_patterns=[], score_threshold=0.0, score_top=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddScorerArgs:
    def test_score_pattern_default_empty(self):
        p = _make_parser()
        ns = p.parse_args([])
        assert ns.score_patterns == []

    def test_score_pattern_single(self):
        p = _make_parser()
        ns = p.parse_args(["--score-pattern", "error:2.0"])
        assert ns.score_patterns == ["error:2.0"]

    def test_score_pattern_multiple(self):
        p = _make_parser()
        ns = p.parse_args(["--score-pattern", "error", "--score-pattern", "warn"])
        assert len(ns.score_patterns) == 2

    def test_score_threshold_default(self):
        p = _make_parser()
        ns = p.parse_args([])
        assert ns.score_threshold == 0.0

    def test_score_threshold_custom(self):
        p = _make_parser()
        ns = p.parse_args(["--score-threshold", "3.5"])
        assert ns.score_threshold == pytest.approx(3.5)

    def test_score_top_default_none(self):
        p = _make_parser()
        ns = p.parse_args([])
        assert ns.score_top is None

    def test_score_top_custom(self):
        p = _make_parser()
        ns = p.parse_args(["--score-top", "10"])
        assert ns.score_top == 10


class TestParseRule:
    def test_pattern_only(self):
        rule = _parse_rule("error")
        assert rule.pattern == "error"
        assert rule.weight == 1.0

    def test_pattern_with_weight(self):
        rule = _parse_rule("critical:5.0")
        assert rule.pattern == "critical"
        assert rule.weight == pytest.approx(5.0)

    def test_invalid_weight_falls_back(self):
        rule = _parse_rule("some:pattern:notafloat")
        assert rule.pattern == "some:pattern"
        assert rule.weight == 1.0


class TestScorerOptsFromArgs:
    def test_empty_patterns_gives_disabled_opts(self):
        opts = scorer_opts_from_args(_make_args())
        assert not opts.enabled()

    def test_rules_parsed_correctly(self):
        args = _make_args(score_patterns=["error:2", "warn"])
        opts = scorer_opts_from_args(args)
        assert len(opts.rules) == 2
        assert opts.rules[0].weight == pytest.approx(2.0)
        assert opts.rules[1].pattern == "warn"

    def test_threshold_forwarded(self):
        args = _make_args(score_threshold=4.0)
        opts = scorer_opts_from_args(args)
        assert opts.threshold == pytest.approx(4.0)

    def test_top_n_forwarded(self):
        args = _make_args(score_top=5)
        opts = scorer_opts_from_args(args)
        assert opts.top_n == 5
