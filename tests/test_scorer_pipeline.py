"""Tests for logslice.scorer_pipeline."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.scorer import ScoreRule, ScorerOptions
from logslice.scorer_pipeline import RankOptions, RankedLine, rank_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, message=text, level=None, timestamp=None, extra={})


def _parse(raw: list[str], opts: RankOptions) -> list[RankedLine]:
    return list(rank_lines([make_line(t) for t in raw], opts))


class TestRankOptions:
    def test_defaults(self):
        o = RankOptions()
        assert o.top_n == 0
        assert o.threshold == 0.0
        assert o.descending is True

    def test_negative_top_n_raises(self):
        with pytest.raises(ValueError):
            RankOptions(top_n=-1)

    def test_negative_threshold_raises(self):
        with pytest.raises(ValueError):
            RankOptions(threshold=-0.5)


class TestRankLines:
    def _opts(self, pattern="error", weight=1.0, **kw) -> RankOptions:
        rules = [ScoreRule(pattern=pattern, weight=weight)]
        return RankOptions(scorer=ScorerOptions(rules=rules), **kw)

    def test_non_matching_excluded_by_threshold(self):
        opts = self._opts(threshold=0.5)
        results = _parse(["hello world", "error occurred"], opts)
        assert len(results) == 1
        assert "error" in results[0].line.raw

    def test_descending_order_default(self):
        rules = [
            ScoreRule(pattern="error", weight=2.0),
            ScoreRule(pattern="warn", weight=1.0),
        ]
        opts = RankOptions(scorer=ScorerOptions(rules=rules))
        results = _parse(["warn only", "error and warn", "nothing"], opts)
        assert results[0].score >= results[1].score

    def test_ascending_order(self):
        rules = [ScoreRule(pattern="error", weight=3.0)]
        opts = RankOptions(scorer=ScorerOptions(rules=rules), descending=False)
        results = _parse(["error here", "no match"], opts)
        assert results[0].score <= results[1].score

    def test_top_n_limits_results(self):
        rules = [ScoreRule(pattern="x", weight=1.0)]
        opts = RankOptions(scorer=ScorerOptions(rules=rules), top_n=1)
        results = _parse(["x", "x x", "x x x"], opts)
        assert len(results) == 1

    def test_top_n_zero_returns_all(self):
        rules = [ScoreRule(pattern="a", weight=1.0)]
        opts = RankOptions(scorer=ScorerOptions(rules=rules), top_n=0)
        results = _parse(["a", "a", "a"], opts)
        assert len(results) == 3

    def test_empty_input_yields_nothing(self):
        opts = self._opts()
        assert _parse([], opts) == []

    def test_ranked_line_lt(self):
        a = RankedLine(line=make_line("a"), score=1.0)
        b = RankedLine(line=make_line("b"), score=2.0)
        assert a < b
