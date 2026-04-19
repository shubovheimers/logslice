"""CLI helpers for the renamer module."""
from __future__ import annotations

import argparse
from typing import List

from logslice.renamer import RenameOptions


def add_rename_args(parser: argparse.ArgumentParser) -> None:
    """Attach rename-related arguments to *parser*."""
    parser.add_argument(
        "--rename-field",
        metavar="OLD=NEW",
        dest="rename_fields",
        action="append",
        default=[],
        help="Rename an extra field key (repeatable).",
    )
    parser.add_argument(
        "--rename-level",
        metavar="NAME",
        dest="rename_level",
        default=None,
        help="Replace the level value with NAME.",
    )
    parser.add_argument(
        "--rename-source",
        metavar="NAME",
        dest="rename_source",
        default=None,
        help="Replace the source value with NAME.",
    )
    parser.add_argument(
        "--strip-prefix",
        metavar="PREFIX",
        dest="strip_prefix",
        default=None,
        help="Strip PREFIX from all (renamed) field keys.",
    )
    parser.add_argument(
        "--strip-suffix",
        metavar="SUFFIX",
        dest="strip_suffix",
        default=None,
        help="Strip SUFFIX from all (renamed) field keys.",
    )


def _parse_mapping(pairs: List[str]) -> dict:
    mapping = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(
                f"--rename-field expects OLD=NEW, got: {pair!r}"
            )
        old, new = pair.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def rename_opts_from_args(args: argparse.Namespace) -> RenameOptions:
    return RenameOptions(
        mapping=_parse_mapping(getattr(args, "rename_fields", []) or []),
        rename_level=getattr(args, "rename_level", None),
        rename_source=getattr(args, "rename_source", None),
        strip_prefix=getattr(args, "strip_prefix", None),
        strip_suffix=getattr(args, "strip_suffix", None),
    )
