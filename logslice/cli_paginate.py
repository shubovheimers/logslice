"""CLI helpers for adding pagination arguments and resolving PaginateOptions."""

from __future__ import annotations

import argparse
from typing import Optional

from logslice.paginator import PaginateOptions


def add_paginate_args(parser: argparse.ArgumentParser) -> None:
    """Register --limit and --offset arguments on *parser*."""
    group = parser.add_argument_group("pagination")
    group.add_argument(
        "--limit",
        metavar="N",
        type=int,
        default=None,
        help="Maximum number of log lines to output.",
    )
    group.add_argument(
        "--offset",
        metavar="N",
        type=int,
        default=0,
        help="Number of matching log lines to skip before outputting (default: 0).",
    )


def paginate_opts_from_args(
    args: argparse.Namespace,
) -> Optional[PaginateOptions]:
    """Build a :class:`PaginateOptions` from parsed CLI *args*.

    Returns ``None`` when neither ``--limit`` nor ``--offset`` was supplied so
    that callers can skip the pagination step entirely.
    """
    limit: Optional[int] = getattr(args, "limit", None)
    offset: int = getattr(args, "offset", 0)

    if limit is None and offset == 0:
        return None

    return PaginateOptions(limit=limit, offset=offset)
