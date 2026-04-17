"""CLI helpers for streak detection."""
from __future__ import annotations

import argparse
from typing import List

from logslice.streaker import StreakOptions


def add_streak_args(parser: argparse.ArgumentParser) -> None:
    """Attach streak-related arguments to *parser*."""
    g = parser.add_argument_group("streak detection")
    g.add_argument(
        "--streak-pattern",
        metavar="REGEX",
        default="",
        help="Emit only lines that form consecutive runs matching REGEX",
    )
    g.add_argument(
        "--streak-min",
        metavar="N",
        type=int,
        default=2,
        help="Minimum run length to qualify as a streak (default: 2)",
    )
    g.add_argument(
        "--streak-case-sensitive",
        action="store_true",
        default=False,
        help="Make streak pattern matching case-sensitive",
    )


def streak_opts_from_args(args: argparse.Namespace) -> StreakOptions:
    return StreakOptions(
        pattern=args.streak_pattern,
        min_length=args.streak_min,
        case_sensitive=args.streak_case_sensitive,
    )
