"""CLI helpers for the windower feature."""
from __future__ import annotations

import argparse
from typing import Optional

from logslice.windower import WindowOptions


def add_window_args(parser: argparse.ArgumentParser) -> None:
    """Attach window-related arguments to *parser*."""
    grp = parser.add_argument_group("windowing")
    grp.add_argument(
        "--window",
        dest="window_size",
        type=int,
        default=0,
        metavar="SECONDS",
        help="aggregate lines into tumbling windows of SECONDS width",
    )
    grp.add_argument(
        "--window-step",
        dest="window_step",
        type=int,
        default=None,
        metavar="SECONDS",
        help="sliding step in seconds (omit for tumbling windows)",
    )
    grp.add_argument(
        "--window-min-lines",
        dest="window_min_lines",
        type=int,
        default=1,
        metavar="N",
        help="only emit windows with at least N lines (default: 1)",
    )


def window_opts_from_args(args: argparse.Namespace) -> Optional[WindowOptions]:
    """Build a WindowOptions from parsed CLI args, or None if disabled."""
    size: int = getattr(args, "window_size", 0)
    if not size:
        return None
    return WindowOptions(
        enabled=True,
        size_seconds=size,
        step_seconds=getattr(args, "window_step", None),
        min_lines=getattr(args, "window_min_lines", 1),
    )
