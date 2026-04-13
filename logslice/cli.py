"""CLI entry point for logslice."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from logslice.reader import open_log_file, iter_lines, count_lines
from logslice.filter import apply_filters
from logslice.formatter import FormatOptions, format_lines
from logslice.stats import collect_stats, format_stats
from logslice.parser import parse_timestamp


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Slice and filter large log files by time, level, or pattern.",
    )
    p.add_argument("file", help="Log file to process (.log or .log.gz)")
    p.add_argument("--start", metavar="DATETIME", help="Include lines at or after this timestamp")
    p.add_argument("--end", metavar="DATETIME", help="Include lines at or before this timestamp")
    p.add_argument(
        "--level",
        metavar="LEVEL",
        help="Filter to this log level (e.g. ERROR, WARNING)",
    )
    p.add_argument("--pattern", metavar="REGEX", help="Only include lines matching this regex")
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Colorise output by log level",
    )
    p.add_argument(
        "--line-numbers",
        action="store_true",
        default=False,
        help="Prefix each output line with its line number",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Print summary statistics after processing",
    )
    p.add_argument(
        "--stats-only",
        action="store_true",
        default=False,
        help="Print only summary statistics, suppress matched output",
    )
    return p


def run(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    start = parse_timestamp(args.start) if args.start else None
    end = parse_timestamp(args.end) if args.end else None

    fmt_opts = FormatOptions(
        color=args.color,
        show_line_numbers=args.line_numbers,
    )

    try:
        fh = open_log_file(args.file)
    except FileNotFoundError:
        print(f"logslice: file not found: {args.file}", file=sys.stderr)
        return 2

    with fh:
        total = count_lines(args.file)
        all_lines = iter_lines(fh)
        filtered = apply_filters(
            all_lines,
            start=start,
            end=end,
            level=args.level,
            pattern=args.pattern,
        )

        if args.stats or args.stats_only:
            matched = list(filtered)
            stats = collect_stats(iter(matched), total_lines=total)
            if not args.stats_only:
                for text in format_lines(iter(matched), fmt_opts):
                    print(text)
            print(format_stats(stats), file=sys.stderr)
        else:
            for text in format_lines(filtered, fmt_opts):
                print(text)

    return 0


def main() -> None:
    sys.exit(run())
