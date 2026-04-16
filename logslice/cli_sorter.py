"""CLI helpers for the sorter feature."""
from __future__ import annotations

import argparse
from typing import Optional

from logslice.sorter import SortOptions


def add_sort_args(parser: argparse.ArgumentParser) -> None:
    """Register --sort-by / --sort-reverse / --sort-buffer onto *parser*."""
    grp = parser.add_argument_group("sorting")
    grp.add_argument(
        "--sort-by",
        metavar="FIELD",
        default=None,
        choices=["timestamp", "level", "lineno"],
        help="Sort output lines by FIELD (timestamp, level, lineno).",
    )
    grp.add_argument(
        "--sort-reverse",
        action="store_true",
        default=False,
        help="Reverse the sort order.",
    )
    grp.add_argument(
        "--sort-buffer",
        metavar="N",
        type=int,
        default=None,
        help="Sort in chunks of N lines instead of buffering the whole file.",
    )


def sort_opts_from_args(args: argparse.Namespace) -> Optional[SortOptions]:
    """Return a :class:`SortOptions` from parsed *args*, or ``None`` if sorting
    was not requested."""
    by = getattr(args, "sort_by", None)
    if by is None:
        return None
    return SortOptions(
        by=by,
        reverse=getattr(args, "sort_reverse", False),
        buffer_size=getattr(args, "sort_buffer", None),
    )
