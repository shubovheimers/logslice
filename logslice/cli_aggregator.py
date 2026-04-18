"""CLI helpers for the aggregator feature."""
from __future__ import annotations
import argparse
from logslice.aggregator import AggregateOptions


def add_aggregate_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("aggregation")
    grp.add_argument(
        "--aggregate",
        action="store_true",
        default=False,
        help="Aggregate log lines into time buckets.",
    )
    grp.add_argument(
        "--bucket-seconds",
        type=int,
        default=60,
        metavar="N",
        help="Bucket size in seconds (default: 60).",
    )
    grp.add_argument(
        "--agg-by-level",
        action="store_true",
        default=False,
        help="Break down bucket counts by log level.",
    )
    grp.add_argument(
        "--agg-pattern",
        default="",
        metavar="REGEX",
        help="Count lines matching REGEX within each bucket.",
    )


def aggregate_opts_from_args(args: argparse.Namespace) -> AggregateOptions:
    return AggregateOptions(
        bucket_seconds=args.bucket_seconds,
        by_level=args.agg_by_level,
        by_pattern=args.agg_pattern,
        enabled=args.aggregate,
    )
