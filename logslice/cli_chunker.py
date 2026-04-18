"""CLI helpers for the chunker module."""
from __future__ import annotations

import argparse

from logslice.chunker import ChunkOptions


def add_chunk_args(parser: argparse.ArgumentParser) -> None:
    """Add chunker arguments to an existing argument parser."""
    grp = parser.add_argument_group("chunking")
    grp.add_argument(
        "--chunk-lines",
        type=int,
        default=0,
        metavar="N",
        help="Split output into chunks of N lines.",
    )
    grp.add_argument(
        "--chunk-seconds",
        type=float,
        default=0.0,
        metavar="S",
        help="Split output into time-window chunks of S seconds.",
    )
    grp.add_argument(
        "--no-partial-chunk",
        action="store_true",
        default=False,
        help="Discard the final partial chunk if it is smaller than the chunk size.",
    )


def chunk_opts_from_args(args: argparse.Namespace) -> ChunkOptions:
    return ChunkOptions(
        max_lines=args.chunk_lines,
        time_window_seconds=args.chunk_seconds,
        include_partial=not args.no_partial_chunk,
    )
