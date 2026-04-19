"""cli_pruner.py – CLI argument helpers for the pruner module."""
from __future__ import annotations

import argparse

from logslice.pruner import PruneOptions


def add_prune_args(parser: argparse.ArgumentParser) -> None:
    """Register --prune-* flags on *parser*."""
    g = parser.add_argument_group("pruner")
    g.add_argument(
        "--prune",
        action="store_true",
        default=False,
        help="Enable line pruning based on minimum message length.",
    )
    g.add_argument(
        "--prune-min-length",
        type=int,
        default=1,
        metavar="N",
        help="Minimum character length a line must have to be kept (default: 1).",
    )
    g.add_argument(
        "--prune-keep-whitespace",
        action="store_true",
        default=False,
        help="Do not strip surrounding whitespace before measuring length.",
    )


def prune_opts_from_args(args: argparse.Namespace) -> PruneOptions:
    return PruneOptions(
        enabled=args.prune,
        min_length=args.prune_min_length,
        strip_whitespace=not args.prune_keep_whitespace,
    )
