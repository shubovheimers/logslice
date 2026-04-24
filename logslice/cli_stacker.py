"""cli_stacker.py — CLI helpers for the stacker module."""
from __future__ import annotations

import argparse
from typing import Optional

from logslice.stacker import StackOptions


def add_stack_args(parser: argparse.ArgumentParser) -> None:
    """Register --stack-lines and --stack-seconds arguments."""
    grp = parser.add_argument_group("stacking")
    grp.add_argument(
        "--stack-lines",
        metavar="N",
        type=int,
        default=0,
        help="Accumulate N lines per stack (0 = disabled).",
    )
    grp.add_argument(
        "--stack-seconds",
        metavar="S",
        type=float,
        default=0.0,
        help="Accumulate lines within S-second windows (0 = disabled).",
    )
    grp.add_argument(
        "--stack-min-lines",
        metavar="M",
        type=int,
        default=1,
        help="Minimum lines required to emit a stack (default: 1).",
    )


def stack_opts_from_args(args: argparse.Namespace) -> Optional[StackOptions]:
    """Build StackOptions from parsed CLI args; return None when disabled."""
    opts = StackOptions(
        max_lines=args.stack_lines,
        seconds=args.stack_seconds,
        min_lines=args.stack_min_lines,
    )
    return opts if opts.enabled else None
