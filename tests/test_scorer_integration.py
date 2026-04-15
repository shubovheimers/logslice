"""Integration tests for scorer + cli_scorer working together."""
from __future__ import annotations

import argparse
from datetime import datetime

from logslice.parser import LogLine
from logslice.cli_scorer import add_scorer_args, scorer_opts_from_args
from logslice.scorer import score_lines


def _make_line(text: str) -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 6, 1, 0, 0, 0),
        level="INFO",
        message=text,
    )


def _parse(argv):
    p = argparse.ArgumentParser()
    add_scorer_args(p)
    return p.parse_args(argv)


class TestScorerIntegration:
    def test_full_pipeline_top1(self):
        ns = _parse(["--score-pattern", "critical:3", "--score-top", "1"])
        opts = scorer_opts_from_args(ns)
        lines = [
            _make_line("everything is fine"),
            _make_line("critical failure detected"),
            _make_line("critical critical meltdown"),
        ]
        result = list(score_lines(lines, opts))
        assert len(result) == 1
        assert "meltdown" in result[0].line.raw

    def test_threshold_excludes_non_matching(self):
        ns = _parse(["--score-pattern", "error:2", "--score-threshold", "1.5"])
        opts = scorer_opts_from_args(ns)
        lines = [
            _make_line("no problems here"),
            _make_line("an error was found"),
        ]
        result = list(score_lines(lines, opts))
        assert len(result) == 1
        assert result[0].score >= 1.5

    def test_multiple_rules_accumulate(self):
        ns = _parse([
            "--score-pattern", "error:1",
            "--score-pattern", "critical:2",
        ])
        opts = scorer_opts_from_args(ns)
        lines = [_make_line("critical error occurred")]
        result = list(score_lines(lines, opts))
        assert result[0].score == 3.0

    def test_no_rules_passthrough_unchanged(self):
        ns = _parse([])
        opts = scorer_opts_from_args(ns)
        lines = [_make_line("line one"), _make_line("line two")]
        result = list(score_lines(lines, opts))
        assert len(result) == 2
        assert all(sl.score == 0.0 for sl in result)
