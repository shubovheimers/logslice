"""CLI helpers for the scroller feature."""
from __future__ import annotations

import argparse
from typing import Optional

from logslice.scroller import ScrollOptions


def add_scroll_args(parser: argparse.ArgumentParser) -> None:
    """Attach scroller arguments to *parser* (or a sub-parser)."""
    grp = parser.add_argument_group("scrolling")
    grp.add_argument(
        "--scroll-window",
        type=int,
        default=50,
        metavar="N",
        help="Number of lines per window (default: 50).",
    )
    grp.add_argument(
        "--scroll-step",
        type=int,
        default=1,
        metavar="N",
        help="Lines to advance between windows (default: 1).",
    )
    grp.add_argument(
        "--scroll-start",
        type=int,
        default=0,
        metavar="N",
        help="0-based line index to start scrolling from (default: 0).",
    )
    grp.add_argument(
        "--scroll-max-windows",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of windows to emit (default: unlimited).",
    )


def scroll_opts_from_args(args: argparse.Namespace) -> Optional[ScrollOptions]:
    """Build a :class:`ScrollOptions` from parsed *args*, or *None* if not used."""
    # Only activate when the caller explicitly set a non-default window size or
    # any of the other scroll flags beyond their defaults.
    if (
        args.scroll_window != 50
        or args.scroll_step != 1
        or args.scroll_start != 0
        or args.scroll_max_windows is not None
    ):
        return ScrollOptions(
            window_size=args.scroll_window,
            step=args.scroll_step,
            start_line=args.scroll_start,
            max_windows=args.scroll_max_windows,
        )
    return None
