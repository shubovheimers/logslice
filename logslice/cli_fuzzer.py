"""CLI helpers for the fuzzy-match filter."""
from __future__ import annotations

import argparse
from logslice.fuzzer import FuzzOptions


def add_fuzz_args(parser: argparse.ArgumentParser) -> None:
    """Register fuzzy-match arguments onto *parser*."""
    g = parser.add_argument_group("fuzzy match")
    g.add_argument(
        "--fuzz",
        metavar="QUERY",
        default=None,
        help="fuzzy-match query string",
    )
    g.add_argument(
        "--fuzz-threshold",
        type=float,
        default=0.3,
        metavar="N",
        help="minimum Dice similarity score (0.0-1.0, default 0.3)",
    )
    g.add_argument(
        "--fuzz-field",
        choices=["raw", "level", "message"],
        default="raw",
        help="log line field to match against (default: raw)",
    )
    g.add_argument(
        "--fuzz-scores",
        action="store_true",
        default=False,
        help="attach similarity score to each matched line's extra dict",
    )


def fuzz_opts_from_args(args: argparse.Namespace) -> FuzzOptions:
    """Build a :class:`FuzzOptions` from parsed *args*."""
    query = args.fuzz or ""
    return FuzzOptions(
        query=query,
        threshold=args.fuzz_threshold,
        field=args.fuzz_field,
        enabled=bool(query),
        scores=args.fuzz_scores,
    )
