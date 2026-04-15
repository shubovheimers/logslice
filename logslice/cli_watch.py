"""CLI integration for the live-watch / tail feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.watchdog import WatchOptions, tail_file
from logslice.formatter import FormatOptions, format_line


def add_watch_subparser(subparsers) -> None:
    """Register the *watch* sub-command."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "watch",
        help="Tail a log file and stream new lines in real time.",
    )
    p.add_argument("file", help="Path to the log file to watch.")
    p.add_argument(
        "--interval",
        type=float,
        default=0.5,
        metavar="SECS",
        help="Poll interval in seconds (default: 0.5).",
    )
    p.add_argument(
        "--max-idle",
        type=float,
        default=None,
        metavar="SECS",
        dest="max_idle",
        help="Exit after SECS seconds with no new data.",
    )
    p.add_argument(
        "--follow-rotated",
        action="store_true",
        default=False,
        dest="follow_rotated",
        help="Re-open the file if rotation is detected.",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Colorize output by log level.",
    )
    p.set_defaults(func=run_watch)


def run_watch(args: argparse.Namespace) -> int:
    """Entry point for the *watch* sub-command."""
    opts = WatchOptions(
        enabled=True,
        poll_interval=args.interval,
        max_idle=args.max_idle,
        follow_rotated=args.follow_rotated,
    )
    fmt = FormatOptions(color=args.color)
    path = Path(args.file)
    if not path.exists():
        print(f"logslice watch: file not found: {path}", file=sys.stderr)
        return 1

    try:
        for log_line in tail_file(path, opts):
            print(format_line(log_line, fmt))
    except KeyboardInterrupt:
        pass
    return 0
