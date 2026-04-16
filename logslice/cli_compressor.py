"""CLI helpers for the compressor feature."""
from __future__ import annotations

import argparse
from logslice.compressor import CompressOptions


def add_compress_args(parser: argparse.ArgumentParser) -> None:
    """Attach compression-related arguments to *parser*."""
    grp = parser.add_argument_group("compression")
    grp.add_argument(
        "--compress",
        action="store_true",
        default=False,
        help="Collapse runs of identical log messages to reduce output volume.",
    )
    grp.add_argument(
        "--compress-min-run",
        type=int,
        default=3,
        metavar="N",
        help="Minimum consecutive identical lines before compressing (default: 3).",
    )
    grp.add_argument(
        "--compress-placeholder",
        default="... [{count} identical lines omitted] ...",
        metavar="TEXT",
        help="Template for the omission summary line (use {count} as placeholder).",
    )


def compress_opts_from_args(args: argparse.Namespace) -> CompressOptions:
    """Build a :class:`CompressOptions` from parsed CLI arguments."""
    return CompressOptions(
        enabled=args.compress,
        min_run=args.compress_min_run,
        placeholder=args.compress_placeholder,
    )
