"""CLI helpers for the tagger feature."""
from __future__ import annotations

import argparse
import json
from typing import List, Optional

from logslice.tagger import TagRule, TaggerOptions, build_tagger_options


def add_tagger_args(parser: argparse.ArgumentParser) -> None:
    """Add tagging-related arguments to an existing argument parser."""
    group = parser.add_argument_group("tagging")
    group.add_argument(
        "--tag",
        dest="tag_rules",
        metavar="TAG:PATTERN",
        action="append",
        default=[],
        help="Tag lines matching PATTERN with TAG (repeatable). "
             "Example: --tag error:ERROR",
    )
    group.add_argument(
        "--tag-rules-file",
        dest="tag_rules_file",
        metavar="FILE",
        default=None,
        help="JSON file containing a list of {tag, pattern} rule objects.",
    )
    group.add_argument(
        "--tag-single",
        dest="tag_single",
        action="store_true",
        default=False,
        help="Apply only the first matching tag per line (default: all).",
    )


def _parse_inline_rules(raw: List[str]) -> List[dict]:
    """Parse 'TAG:PATTERN' strings into rule dicts."""
    rules = []
    for item in raw:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid --tag value {item!r}: expected TAG:PATTERN"
            )
        tag, _, pattern = item.partition(":")
        rules.append({"tag": tag.strip(), "pattern": pattern.strip()})
    return rules


def tagger_opts_from_args(args: argparse.Namespace) -> Optional[TaggerOptions]:
    """Build TaggerOptions from parsed CLI args; returns None if no rules."""
    rules: List[dict] = []

    if getattr(args, "tag_rules", None):
        rules.extend(_parse_inline_rules(args.tag_rules))

    rules_file: Optional[str] = getattr(args, "tag_rules_file", None)
    if rules_file:
        with open(rules_file, "r", encoding="utf-8") as fh:
            file_rules = json.load(fh)
        if not isinstance(file_rules, list):
            raise ValueError("tag-rules-file must contain a JSON array of rule objects")
        rules.extend(file_rules)

    if not rules:
        return None

    multi = not getattr(args, "tag_single", False)
    return build_tagger_options(rules=rules, multi=multi)
