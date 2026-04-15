"""CLI helpers for the relevance scorer feature."""
from __future__ import annotations

import argparse
from typing import List

from logslice.scorer import ScoreRule, ScorerOptions


def add_scorer_args(parser: argparse.ArgumentParser) -> None:
    """Attach scorer-related arguments to *parser*."""
    grp = parser.add_argument_group("relevance scoring")
    grp.add_argument(
        "--score-pattern",
        metavar="PATTERN:WEIGHT",
        action="append",
        dest="score_patterns",
        default=[],
        help="Pattern and optional weight (e.g. 'error:2.0'). Repeatable.",
    )
    grp.add_argument(
        "--score-threshold",
        type=float,
        default=0.0,
        metavar="N",
        help="Minimum score for a line to be included (default: 0).",
    )
    grp.add_argument(
        "--score-top",
        type=int,
        default=None,
        metavar="N",
        help="Return only the top-N highest-scoring lines.",
    )


def _parse_rule(spec: str) -> ScoreRule:
    """Parse 'PATTERN' or 'PATTERN:WEIGHT' into a ScoreRule."""
    if ":" in spec:
        parts = spec.rsplit(":", 1)
        try:
            weight = float(parts[1])
            return ScoreRule(pattern=parts[0], weight=weight)
        except ValueError:
            pass
    return ScoreRule(pattern=spec)


def scorer_opts_from_args(args: argparse.Namespace) -> ScorerOptions:
    rules: List[ScoreRule] = [_parse_rule(s) for s in (args.score_patterns or [])]
    return ScorerOptions(
        rules=rules,
        threshold=args.score_threshold,
        top_n=args.score_top,
    )
