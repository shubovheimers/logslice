"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice.reader import iter_lines
from logslice.filter import apply_filters


DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]


def_(value:
    forn        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime '{value}'. "
        "Expected format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS"
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Slice and filter large log files by time, level, or pattern.",
    )
    p.add_argument("file", help="Path to the log file (.log, .gz, .bz2)")
    p.add_argument(
        "--start", metavar="DATETIME", type=parse_datetime_arg,
        help="Include lines at or after this timestamp",
    )
    p.add_argument(
        "--end", metavar="DATETIME", type=parse_datetime_arg,
        help="Include lines at or before this timestamp",
    )
    p.add_argument(
        "--level", metavar="LEVEL",
        help="Filter to this log level (e.g. ERROR, WARN)",
    )
    p.add_argument(
        "--pattern", metavar="REGEX",
        help="Only include lines matching this regular expression",
    )
    p.add_argument(
        "--include-unparseable", action="store_true",
        help="Include lines whose timestamp could not be parsed",
    )
    return p


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    skip = not args.include_unparseable
    try:
        lines = iter_lines(args.file, skip_unparseable=skip)
        filtered = apply_filters(
            lines,
            start=args.start,
            end=args.end,
            level=args.level,
            pattern=args.pattern,
        )
        for log_line in filtered:
            print(log_line.raw)
    except FileNotFoundError:
        print(f"logslice: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
