"""CLI helpers for the flattener feature."""
from __future__ import annotations

import argparse

from logslice.flattener import FlattenOptions


def add_flatten_args(parser: argparse.ArgumentParser) -> None:
    """Attach flatten-related arguments to *parser*."""
    grp = parser.add_argument_group("flattening")
    grp.add_argument(
        "--flatten",
        action="store_true",
        default=False,
        help="Merge continuation lines into the preceding log record.",
    )
    grp.add_argument(
        "--flatten-pattern",
        metavar="REGEX",
        default=r"^\d{4}-\d{2}-\d{2}",
        help="Regex that identifies the start of a new log record "
             "(default: ISO date prefix).",
    )
    grp.add_argument(
        "--flatten-separator",
        metavar="SEP",
        default=" ",
        help="String inserted between joined lines (default: single space).",
    )
    grp.add_argument(
        "--flatten-max-continuation",
        metavar="N",
        type=int,
        default=50,
        help="Maximum continuation lines absorbed per record (default: 50).",
    )


def flatten_opts_from_args(args: argparse.Namespace) -> FlattenOptions:
    """Build a :class:`FlattenOptions` from parsed CLI *args*."""
    return FlattenOptions(
        enabled=args.flatten,
        record_start_pattern=args.flatten_pattern,
        join_separator=args.flatten_separator,
        max_continuation=args.flatten_max_continuation,
    )
