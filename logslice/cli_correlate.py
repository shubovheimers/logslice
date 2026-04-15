"""CLI sub-command: correlate — filter log lines by a shared correlation ID."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.correlator import CorrelateOptions, iter_correlated
from logslice.reader import iter_lines


def add_correlate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "correlate",
        help="Extract all log lines sharing a correlation ID.",
    )
    p.add_argument("file", help="Log file to read (plain text or .gz).")
    p.add_argument(
        "correlation_id",
        help="The correlation ID value to filter on.",
    )
    p.add_argument(
        "--field",
        default="request_id",
        help="Metadata key that holds the correlation ID (default: request_id).",
    )
    p.add_argument(
        "--pattern",
        default=None,
        help="Regex with an optional capture group to extract the ID from raw text.",
    )
    p.set_defaults(func=run_correlate)


def run_correlate(args: argparse.Namespace) -> int:
    """Entry point for the 'correlate' sub-command."""
     = CorrelateOptions(
        field=args.field,
        pattern=args.pattern,
    )

    count = 0
    try:
        lines = iter_lines(args.file)
        for line in iter_correlated(lines, opts, args.correlation_id):
            sys.stdout.write(line.raw + "\n")
            count += 1
    except FileNotFoundError:
        sys.stderr.write(f"logslice correlate: file not found: {args.file}\n")
        return 1

    sys.stderr.write(f"logslice correlate: {count} line(s) matched.\n")
    return 0
