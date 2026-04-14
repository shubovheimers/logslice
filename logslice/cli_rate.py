"""CLI helpers for the rate-counter feature."""

from __future__ import annotations

import argparse
from typing import Optional

from logslice.rate_counter import RateOptions


def add_rate_args(parser: argparse.ArgumentParser) -> None:
    """Register --rate-* arguments onto an existing (sub)parser."""
    grp = parser.add_argument_group("rate filtering")
    grp.add_argument(
        "--rate-filter",
        action="store_true",
        default=False,
        help="Enable rate-based line filtering.",
    )
    grp.add_argument(
        "--rate-window",
        type=int,
        default=60,
        metavar="SECS",
        help="Sliding window size in seconds for rate calculation (default: 60).",
    )
    grp.add_argument(
        "--rate-bucket",
        type=int,
        default=1,
        metavar="SECS",
        help="Bucket granularity in seconds (default: 1).",
    )
    grp.add_argument(
        "--min-rate",
        type=float,
        default=None,
        metavar="N",
        help="Only emit lines whose per-bucket rate is >= N events/sec.",
    )


def rate_opts_from_args(args: argparse.Namespace) -> RateOptions:
    """Build a RateOptions from parsed CLI arguments."""
    enabled: bool = getattr(args, "rate_filter", False)
    window: int = getattr(args, "rate_window", 60)
    bucket: int = getattr(args, "rate_bucket", 1)
    min_rate: Optional[float] = getattr(args, "min_rate", None)

    if min_rate is not None:
        enabled = True

    return RateOptions(
        enabled=enabled,
        window_seconds=window,
        bucket_seconds=bucket,
        min_rate=min_rate,
    )
