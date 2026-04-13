"""CLI sub-command: split — divide a log file into smaller parts."""

from __future__ import annotations

import argparse
from datetime import timedelta
from typing import Optional

from logslice.reader import iter_lines
from logslice.splitter import SplitOptions, split_by_lines, split_by_time, write_chunks


def add_split_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "split",
        help="Split a log file into smaller chunks.",
    )
    p.add_argument("file", help="Path to the log file to split.")
    p.add_argument(
        "--lines",
        type=int,
        default=None,
        metavar="N",
        help="Split every N lines.",
    )
    p.add_argument(
        "--time-window",
        type=int,
        default=None,
        metavar="SECONDS",
        help="Split on gaps larger than SECONDS between log entries.",
    )
    p.add_argument(
        "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory to write output parts (default: current directory).",
    )
    p.add_argument(
        "--prefix",
        default="part",
        help="Filename prefix for output parts (default: 'part').",
    )
    p.add_argument(
        "--suffix",
        default=".log",
        help="Filename suffix for output parts (default: '.log').",
    )
    p.set_defaults(func=run_split)


def run_split(args: argparse.Namespace) -> int:
    """Entry point for the *split* sub-command."""
    if args.lines is None and args.time_window is None:
        print("error: supply --lines or --time-window")
        return 1

    opts = SplitOptions(
        max_lines=args.lines,
        time_window=timedelta(seconds=args.time_window) if args.time_window else None,
        output_dir=args.output_dir,
        prefix=args.prefix,
        suffix=args.suffix,
    )

    lines = list(iter_lines(args.file))

    if opts.max_lines is not None:
        chunks = split_by_lines(lines, opts)
    else:
        chunks = split_by_time(lines, opts)

    paths = write_chunks(chunks, opts)
    for p in paths:
        print(p)
    print(f"Split into {len(paths)} part(s).")
    return 0
