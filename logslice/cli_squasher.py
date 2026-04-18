"""CLI helpers for the squasher feature."""
from __future__ import annotations

import argparse

from logslice.squasher import SquashOptions


def add_squash_args(parser: argparse.ArgumentParser) -> None:
    """Register squash-related arguments on *parser*."""
    g = parser.add_argument_group("squash")
    g.add_argument(
        "--squash",
        action="store_true",
        default=False,
        help="Merge consecutive lines that share the same log level.",
    )
    g.add_argument(
        "--squash-separator",
        default=" | ",
        metavar="SEP",
        help="Separator used when joining squashed messages (default: ' | ').",
    )
    g.add_argument(
        "--squash-max-group",
        type=int,
        default=50,
        metavar="N",
        help="Maximum number of lines to merge into one group (default: 50).",
    )


def squash_opts_from_args(args: argparse.Namespace) -> SquashOptions:
    return SquashOptions(
        enabled=args.squash,
        by_level=True,
        separator=args.squash_separator,
        max_group=args.squash_max_group,
    )
