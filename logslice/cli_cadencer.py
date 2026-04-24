"""CLI helpers for the cadencer feature."""
from __future__ import annotations

import argparse

from logslice.cadencer import CadenceOptions


def add_cadence_args(parser: argparse.ArgumentParser) -> None:
    """Register cadencer arguments onto *parser*."""
    grp = parser.add_argument_group("cadencer")
    grp.add_argument(
        "--cadence",
        metavar="LPS",
        type=float,
        default=0.0,
        help="Limit output to LPS lines per second (0 = unlimited).",
    )
    grp.add_argument(
        "--cadence-burst",
        metavar="N",
        type=int,
        default=1,
        help="Emit N lines before each sleep (default: 1).",
    )


def cadence_opts_from_args(args: argparse.Namespace) -> CadenceOptions:
    """Build a :class:`CadenceOptions` from parsed CLI *args*."""
    return CadenceOptions(
        lines_per_second=args.cadence,
        burst=args.cadence_burst,
    )
