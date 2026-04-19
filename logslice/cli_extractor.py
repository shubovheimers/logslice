"""CLI helpers for the field extractor."""
from __future__ import annotations

import argparse
from typing import List

from logslice.extractor import ExtractOptions


def add_extract_args(parser: argparse.ArgumentParser) -> None:
    """Register --extract-pattern / --extract-prefix / --extract-overwrite."""
    parser.add_argument(
        "--extract-pattern",
        dest="extract_patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Named-group regex to extract fields from each log line (repeatable).",
    )
    parser.add_argument(
        "--extract-prefix",
        dest="extract_prefix",
        default="field_",
        metavar="PREFIX",
        help="Prefix added to extracted field names (default: 'field_').",
    )
    parser.add_argument(
        "--extract-overwrite",
        dest="extract_overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing extra fields with extracted values.",
    )


def extract_opts_from_args(args: argparse.Namespace) -> ExtractOptions:
    """Build an :class:`ExtractOptions` from parsed CLI args."""
    return ExtractOptions(
        patterns=list(args.extract_patterns),
        prefix=args.extract_prefix,
        overwrite=args.extract_overwrite,
    )
