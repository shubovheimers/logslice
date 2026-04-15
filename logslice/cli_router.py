"""CLI integration for the log router."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.router import RouteRule, RouterOptions, collect_routed
from logslice.reader import iter_lines


def _parse_rules(raw: List[str]) -> List[RouteRule]:
    """Parse rule strings of the form 'channel:pattern' or 'channel@level'."""
    rules: List[RouteRule] = []
    for spec in raw:
        if ":" in spec:
            channel, pattern = spec.split(":", 1)
            rules.append(RouteRule(channel=channel.strip(), pattern=pattern.strip()))
        elif "@" in spec:
            channel, level = spec.split("@", 1)
            rules.append(RouteRule(channel=channel.strip(), level=level.strip()))
        else:
            raise argparse.ArgumentTypeError(
                f"Invalid rule {spec!r}. Use 'channel:pattern' or 'channel@LEVEL'."
            )
    return rules


def add_router_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("route", help="Route log lines to named channels")
    p.add_argument(
        "file",
        help="Log file to process",
    )
    p.add_argument(
        "--rule",
        dest="rules",
        metavar="SPEC",
        action="append",
        default=[],
        help="Routing rule: 'channel:pattern' or 'channel@LEVEL'",
    )
    p.add_argument(
        "--default-channel",
        default="default",
        help="Channel name for unmatched lines (default: 'default')",
    )
    p.add_argument(
        "--no-stop",
        dest="stop_on_first_match",
        action="store_false",
        default=True,
        help="Continue matching rules after the first match",
    )
    p.set_defaults(func=run_router)


def run_router(args: argparse.Namespace) -> int:
    try:
        rules = _parse_rules(args.rules)
    except argparse.ArgumentTypeError as exc:
        print(f"logslice route: {exc}", file=sys.stderr)
        return 1

    opts = RouterOptions(
        rules=rules,
        default_channel=args.default_channel,
        stop_on_first_match=args.stop_on_first_match,
    )

    lines = iter_lines(args.file)
    routed = collect_routed(lines, opts)

    for channel in sorted(routed):
        bucket = routed[channel]
        print(f"[{channel}] {len(bucket)} line(s)")
        for line in bucket:
            print(f"  {line.raw}")

    return 0
