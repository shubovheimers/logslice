"""CLI sub-command: summarize a log file."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from logslice.reader import iter_lines
from logslice.summarizer import SummaryOptions, format_summary, summarize_lines


def add_summarize_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *summarize* sub-command onto *subparsers*."""
    p = subparsers.add_parser(
        "summarize",
        help="Print a statistical summary of a log file.",
    )
    p.add_argument("file", help="Path to the log file (plain or .gz).")
    p.add_argument(
        "--top-n",
        type=int,
        default=10,
        metavar="N",
        help="Number of top repeated messages to show (default: 10).",
    )
    p.add_argument(
        "--no-levels",
        action="store_true",
        default=False,
        help="Skip level breakdown.",
    )
    p.add_argument(
        "--no-patterns",
        action="store_true",
        default=False,
        help="Skip top-message breakdown.",
    )
    p.set_defaults(func=run_summarize)


def run_summarize(args: argparse.Namespace) -> int:
    """Execute the summarize sub-command; returns an exit code."""
    opts = SummaryOptions(
        top_n=args.top_n,
        count_levels=not args.no_levels,
        count_patterns=not args.no_patterns,
    )

    try:
        lines = iter_lines(args.file)
        summary = summarize_lines(lines, opts)
    except FileNotFoundError:
        print(f"logslice: file not found: {args.file}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"logslice: {exc}", file=sys.stderr)
        return 1

    print(format_summary(summary))
    return 0
