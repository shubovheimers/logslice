"""CLI sub-command: pivot — frequency table of a log field."""
from __future__ import annotations

import argparse
import sys

from logslice.pivotter import PivotOptions, format_pivot, pivot_lines
from logslice.reader import iter_lines


def add_pivot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("pivot", help="Show a frequency table for a log field")
    p.add_argument("file", help="Log file to pivot")
    p.add_argument(
        "--by",
        default="level",
        help="Field to pivot on: level, source, or an extra-field name (default: level)",
    )
    p.add_argument(
        "--pattern",
        default=None,
        help="Regex with a named group 'key' to extract pivot values from raw text",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        dest="top_n",
        help="Show only the top N entries (0 = all)",
    )
    p.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Hide entries with fewer than this many occurrences",
    )


def run_pivot(args: argparse.Namespace) -> int:
    opts = PivotOptions(
        by=args.by,
        pattern=args.pattern,
        top_n=args.top_n,
        min_count=args.min_count,
    )
    lines = list(iter_lines(args.file))
    table = pivot_lines(lines, opts)
    for row in format_pivot(table, total=len(lines)):
        print(row)
    return 0
