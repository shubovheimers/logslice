"""CLI helpers for the dispatcher feature."""
from __future__ import annotations

import argparse
from typing import List

from logslice.dispatcher import DispatchOptions


def add_dispatcher_args(parser: argparse.ArgumentParser) -> None:
    """Attach dispatcher-related arguments to *parser*."""
    grp = parser.add_argument_group("dispatcher")
    grp.add_argument(
        "--dispatch-channel",
        metavar="CHANNEL",
        default="default",
        help="Named channel to dispatch log lines on (default: %(default)s).",
    )
    grp.add_argument(
        "--dispatch-stop-first",
        action="store_true",
        default=False,
        help="Stop after the first matching handler per line.",
    )


def dispatcher_opts_from_args(args: argparse.Namespace) -> DispatchOptions:
    """Build :class:`DispatchOptions` from parsed CLI *args*."""
    return DispatchOptions(
        stop_on_first_match=args.dispatch_stop_first,
        default_channel=args.dispatch_channel,
    )
