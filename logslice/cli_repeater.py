"""CLI helpers for the repeater feature."""
from __future__ import annotations

import argparse
from typing import Iterator

from logslice.parser import LogLine
from logslice.repeater import RepeatOptions, RepeatMatch, find_repeats


def add_repeat_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("repeat detection")
    grp.add_argument(
        "--repeat",
        action="store_true",
        default=False,
        help="Enable repeated-line detection.",
    )
    grp.add_argument(
        "--repeat-window",
        type=int,
        default=10,
        metavar="N",
        help="Look-back window size for repeat detection (default: 10).",
    )
    grp.add_argument(
        "--repeat-min",
        type=int,
        default=2,
        metavar="N",
        help="Minimum occurrences within window to flag as repeat (default: 2).",
    )
    grp.add_argument(
        "--repeat-key",
        nargs="+",
        default=["level", "message"],
        metavar="FIELD",
        help="Fields used to identify duplicate lines (default: level message).",
    )


def repeat_opts_from_args(args: argparse.Namespace) -> RepeatOptions:
    return RepeatOptions(
        enabled=args.repeat,
        window=args.repeat_window,
        min_repeats=args.repeat_min,
        key_fields=tuple(args.repeat_key),
    )


def run_repeat(lines: Iterator[LogLine], opts: RepeatOptions) -> Iterator[str]:
    """Yield formatted summary lines for detected repeats."""
    for match in find_repeats(lines, opts):
        ts = match.line.timestamp.isoformat() if match.line.timestamp else "?"
        yield (
            f"[REPEAT x{match.count}] {ts} "
            f"[{match.line.level or '?'}] {match.line.message}"
        )
