"""CLI helpers for the replayer feature."""

from __future__ import annotations

import argparse
from typing import Optional

from logslice.replayer import ReplayOptions


def add_replay_args(parser: argparse.ArgumentParser) -> None:
    """Attach replay-related arguments to *parser*."""
    grp = parser.add_argument_group("replay")
    grp.add_argument(
        "--replay",
        action="store_true",
        default=False,
        help="Replay log lines with timing delays matching original timestamps.",
    )
    grp.add_argument(
        "--replay-speed",
        type=float,
        default=1.0,
        metavar="FACTOR",
        help="Speed multiplier for replay (default: 1.0). Use 2.0 for double speed.",
    )
    grp.add_argument(
        "--replay-max-delay",
        type=float,
        default=5.0,
        metavar="SECS",
        help="Maximum seconds to wait between lines during replay (default: 5).",
    )
    grp.add_argument(
        "--replay-real-time",
        action="store_true",
        default=False,
        help="Use real elapsed time between log lines, ignoring --replay-speed.",
    )


def replay_opts_from_args(args: argparse.Namespace) -> Optional[ReplayOptions]:
    """Build a :class:`ReplayOptions` from parsed CLI arguments.

    Returns *None* when replay is not requested.
    """
    if not getattr(args, "replay", False):
        return None
    return ReplayOptions(
        enabled=True,
        speed=args.replay_speed,
        max_delay=args.replay_max_delay,
        real_time=args.replay_real_time,
    )
