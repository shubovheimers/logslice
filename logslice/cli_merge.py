"""CLI sub-command: merge multiple log files into a single time-ordered stream."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.merger import MergeOptions, merge_logs
from logslice.reader import iter_lines
from logslice.output import write_lines
from logslice.formatter import FormatOptions, format_lines


def add_merge_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'merge' sub-command on an existing subparsers action."""
    p = subparsers.add_parser(
        "merge",
        help="Merge multiple log files into a single time-ordered stream.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Log files to merge (plain or .gz).",
    )
    p.add_argument(
        "--tag",
        action="store_true",
        default=False,
        help="Prefix each line with its source filename.",
    )
    p.add_argument(
        "--output", "-o",
        default="-",
        metavar="FILE",
        help="Output file path (default: stdout).",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Colorize log levels in output.",
    )
    p.set_defaults(func=run_merge)


def run_merge(args: argparse.Namespace) -> int:
    """Entry point for the merge sub-command.

    Returns:
        Exit code (0 on success, non-zero on error).
    """
    sources = []
    for path in args.files:
        try:
            label = path
            lines = iter_lines(path)
            sources.append((label, lines))
        except OSError as exc:
            print(f"logslice merge: cannot open {path!r}: {exc}", file=sys.stderr)
            return 1

    opts = MergeOptions(tag_source=getattr(args, "tag", False))
    merged = merge_logs(sources, opts=opts)

    fmt_opts = FormatOptions(color=getattr(args, "color", False))
    formatted = format_lines(merged, fmt_opts)

    output_path = getattr(args, "output", "-")
    count = write_lines(formatted, output_path)
    return 0
