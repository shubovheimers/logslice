"""CLI helpers for the archive sub-command."""
from __future__ import annotations

import argparse
from typing import Sequence

from logslice.archiver import ArchiveOptions, archive_lines
from logslice.reader import iter_lines
from logslice.filter import apply_filters


def add_archive_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "archive",
        help="Compress and archive log lines to a file.",
    )
    p.add_argument("input", help="Path to the input log file.")
    p.add_argument("-o", "--output", required=True, dest="output", help="Destination archive path.")
    p.add_argument(
        "--compression",
        choices=["gz", "bz2", "xz", "none"],
        default="gz",
        help="Compression format (default: gz).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing archive if present.",
    )
    p.add_argument("--level", default=None, help="Filter by log level before archiving.")
    p.add_argument("--pattern", default=None, help="Filter by regex pattern before archiving.")
    p.set_defaults(func=run_archive)


def run_archive(args: argparse.Namespace) -> int:
    opts = ArchiveOptions(
        output_path=args.output,
        compression=args.compression,
        overwrite=args.overwrite,
    )

    lines = iter_lines(args.input)
    lines = apply_filters(
        lines,
        level=args.level,
        pattern=args.pattern,
    )

    count = archive_lines(lines, opts)
    dest = opts.resolved_path()
    print(f"Archived {count} line(s) to {dest}")
    return 0
