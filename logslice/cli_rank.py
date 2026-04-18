"""CLI helpers for the rank/score sub-command."""
from __future__ import annotations

import argparse
from typing import List

from logslice.scorer import ScoreRule, ScorerOptions
from logslice.scorer_pipeline import RankOptions


def add_rank_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("rank", help="Score and rank log lines by pattern weight")
    p.add_argument(
        "--score-pattern",
        metavar="PATTERN:WEIGHT",
        dest="score_patterns",
        action="append",
        default=[],
        help="Pattern and weight separated by colon (repeatable)",
    )
    p.add_argument(
        "--top-n",
        type=int,
        default=0,
        help="Return only the top N results (0 = all)",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum score to include a line",
    )
    p.add_argument(
        "--ascending",
        action="store_true",
        default=False,
        help="Sort lowest score first instead of highest",
    )


def _parse_rules(raw: List[str]) -> List[ScoreRule]:
    rules: List[ScoreRule] = []
    for token in raw:
        if ":" not in token:
            raise ValueError(f"Expected PATTERN:WEIGHT, got {token!r}")
        pattern, _, weight_str = token.rpartition(":")
        rules.append(ScoreRule(pattern=pattern, weight=float(weight_str)))
    return rules


def rank_opts_from_args(args: argparse.Namespace) -> RankOptions:
    rules = _parse_rules(getattr(args, "score_patterns", []))
    scorer = ScorerOptions(rules=rules)
    return RankOptions(
        scorer=scorer,
        top_n=args.top_n,
        threshold=args.threshold,
        descending=not args.ascending,
    )
