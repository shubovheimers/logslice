"""CLI helpers for the clamper feature."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Optional

from logslice.clamper import ClampOptions


def add_clamp_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("timestamp clamping")
    grp.add_argument(
        "--clamp-floor",
        metavar="DATETIME",
        default=None,
        help="Replace timestamps earlier than this with the floor value (ISO-8601).",
    )
    grp.add_argument(
        "--clamp-ceiling",
        metavar="DATETIME",
        default=None,
        help="Replace timestamps later than this with the ceiling value (ISO-8601).",
    )
    grp.add_argument(
        "--clamp-drop",
        action="store_true",
        default=False,
        help="Drop out-of-range lines instead of replacing their timestamp.",
    )


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Cannot parse datetime: {value!r}")


def clamp_opts_from_args(args: argparse.Namespace) -> ClampOptions:
    floor = _parse_dt(getattr(args, "clamp_floor", None))
    ceiling = _parse_dt(getattr(args, "clamp_ceiling", None))
    drop = getattr(args, "clamp_drop", False)
    enabled = floor is not None or ceiling is not None
    return ClampOptions(
        enabled=enabled,
        floor=floor,
        ceiling=ceiling,
        replace_with_bound=not drop,
    )
