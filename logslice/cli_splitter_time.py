"""CLI helpers for time-based log slicing."""
from __future__ import annotations

import argparse
from typing import List

from logslice.splitter_time import TimeSliceOptions


def add_time_slice_args(parser: argparse.ArgumentParser) -> None:
    """Register time-slice arguments on *parser*."""
    grp = parser.add_argument_group("time slicing")
    grp.add_argument(
        "--slice-window",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Split output into fixed time windows of SECONDS duration (0 = disabled).",
    )
    grp.add_argument(
        "--slice-keep-empty",
        action="store_true",
        default=False,
        help="Emit empty time windows (default: skip them).",
    )


def time_slice_opts_from_args(args: argparse.Namespace) -> TimeSliceOptions | None:
    """Return a :class:`TimeSliceOptions` from parsed *args*, or ``None`` if disabled."""
    window: int = getattr(args, "slice_window", 0)
    if not window:
        return None
    keep_empty: bool = getattr(args, "slice_keep_empty", False)
    return TimeSliceOptions(
        window_seconds=window,
        drop_empty=not keep_empty,
    )
