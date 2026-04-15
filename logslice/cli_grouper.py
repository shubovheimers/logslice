"""CLI helpers for the grouper feature."""
from __future__ import annotations

import argparse
from typing import List

from logslice.grouper import GroupOptions, iter_groups
from logslice.parser import LogLine


def add_grouper_args(parser: argparse.ArgumentParser) -> None:
    """Attach grouper arguments to *parser*."""
    g = parser.add_argument_group("grouping")
    g.add_argument(
        "--group-by-field",
        metavar="FIELD",
        default=None,
        help="Group lines by a key present in the parsed extra fields.",
    )
    g.add_argument(
        "--group-by-level",
        action="store_true",
        default=False,
        help="Group lines by their log level.",
    )
    g.add_argument(
        "--group-window",
        metavar="SECONDS",
        type=int,
        default=None,
        help="Group lines into fixed-size time windows (seconds).",
    )


def grouper_opts_from_args(args: argparse.Namespace) -> GroupOptions:
    return GroupOptions(
        by_field=getattr(args, "group_by_field", None),
        by_level=getattr(args, "group_by_level", False),
        window_seconds=getattr(args, "group_window", None),
    )


def run_grouper(lines: List[LogLine], opts: GroupOptions) -> None:
    """Print grouped output to stdout."""
    if not opts.enabled:
        for line in lines:
            print(line.raw)
        return

    for key, members in iter_groups(lines, opts):
        print(f"=== Group: {key} ({len(members)} lines) ===")
        for line in members:
            print(line.raw)
