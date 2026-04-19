"""CLI helpers for the mapper module."""
from __future__ import annotations

import argparse
from typing import List

from logslice.mapper import MapOptions, MapRule


def _parse_rules(raw: List[str]) -> List[MapRule]:
    """Parse 'field=pattern' strings into MapRule objects."""
    rules: List[MapRule] = []
    for item in raw:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid map rule {item!r}: expected 'field=pattern'"
            )
        field, _, pattern = item.partition("=")
        rules.append(MapRule(target_field=field.strip(), expression=pattern.strip()))
    return rules


def add_mapper_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("field mapping")
    grp.add_argument(
        "--map",
        dest="map_rules",
        metavar="FIELD=PATTERN",
        action="append",
        default=[],
        help="Extract regex capture into a named field (repeatable)",
    )
    grp.add_argument(
        "--map-prefix",
        dest="map_prefix",
        default="map_",
        help="Prefix for mapped field names (default: 'map_')",
    )
    grp.add_argument(
        "--map-overwrite",
        dest="map_overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing fields when mapping",
    )


def mapper_opts_from_args(args: argparse.Namespace) -> MapOptions:
    rules = _parse_rules(getattr(args, "map_rules", []) or [])
    return MapOptions(
        rules=rules,
        prefix=getattr(args, "map_prefix", "map_"),
        overwrite=getattr(args, "map_overwrite", False),
    )
