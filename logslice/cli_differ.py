"""CLI sub-command: diff two log files."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.differ import DiffOptions, DiffResult, diff_log_sequences
from logslice.reader import iter_lines


_TAG_COLORS = {
    ">": "\033[32m",  # green  — added
    "<": "\033[31m",  # red    — removed
    "=": "\033[90m",  # grey   — common
}
_RESET = "\033[0m"


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "diff",
        help="Compare two log files and show added, removed, or common lines.",
    )
    p.add_argument("left", help="Base log file (the 'before' file).")
    p.add_argument("right", help="New log file (the 'after' file).")
    p.add_argument(
        "--mode",
        choices=["added", "removed", "common"],
        default="added",
        help="Which lines to emit (default: added).",
    )
    p.add_argument(
        "--no-ignore-timestamps",
        dest="ignore_timestamps",
        action="store_false",
        default=True,
        help="Include timestamps when comparing lines.",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Colorize output by diff tag.",
    )
    p.set_defaults(func=run_diff)


def run_diff(args: argparse.Namespace) -> int:
    opts = DiffOptions(
        mode=args.mode,
        ignore_timestamps=args.ignore_timestamps,
    )

    try:
        left_lines = list(iter_lines(args.left))
        right_lines = list(iter_lines(args.right))
    except FileNotFoundError as exc:
        print(f"logslice diff: {exc}", file=sys.stderr)
        return 1

    results: List[DiffResult] = list(diff_log_sequences(left_lines, right_lines, opts))

    if not results:
        return 0

    for result in results:
        line_text = result.line.raw
        if args.color:
            color = _TAG_COLORS.get(result.tag, "")
            print(f"{color}{result.tag} {line_text}{_RESET}")
        else:
            print(f"{result.tag} {line_text}")

    return 0
