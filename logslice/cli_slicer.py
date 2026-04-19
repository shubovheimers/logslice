"""CLI helpers for the line-range slicer."""
from __future__ import annotations

import argparse

from logslice.slicer import SliceOptions


def add_slice_args(parser: argparse.ArgumentParser) -> None:
    """Attach --slice-start, --slice-end, --slice-step to *parser*."""
    g = parser.add_argument_group("line slicer")
    g.add_argument(
        "--slice-start",
        type=int,
        default=0,
        metavar="N",
        help="First line index to include (0-based, default 0).",
    )
    g.add_argument(
        "--slice-end",
        type=int,
        default=None,
        metavar="N",
        help="Exclusive end line index (default: EOF).",
    )
    g.add_argument(
        "--slice-step",
        type=int,
        default=1,
        metavar="N",
        help="Take every Nth line within the slice (default 1).",
    )


def slice_opts_from_args(args: argparse.Namespace) -> SliceOptions:
    return SliceOptions(
        start_line=args.slice_start,
        end_line=args.slice_end,
        step=args.slice_step,
    )
