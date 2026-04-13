"""CLI sub-command: classify — tag and group log lines by named rules."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import List

from logslice.classifier import ClassifyOptions, ClassifyRule, classify_lines
from logslice.reader import iter_lines


def add_classify_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *classify* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "classify",
        help="Tag log lines with a category based on pattern rules.",
    )
    p.add_argument(
        "file",
        help="Log file to classify (plain or .gz).",
    )
    p.add_argument(
        "-r", "--rule",
        dest="rules",
        metavar="NAME:PATTERN",
        action="append",
        default=[],
        help="Rule in NAME:PATTERN format; may be repeated.",
    )
    p.add_argument(
        "--default",
        dest="default_category",
        default="uncategorised",
        metavar="CATEGORY",
        help="Category assigned when no rule matches (default: uncategorised).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a category count summary instead of tagged lines.",
    )
    p.set_defaults(func=run_classify)


def _parse_rules(raw: List[str]) -> List[ClassifyRule]:
    rules: List[ClassifyRule] = []
    for item in raw:
        if ":" not in item:
            print(f"[logslice] Skipping invalid rule (expected NAME:PATTERN): {item!r}",
                  file=sys.stderr)
            continue
        name, _, pattern = item.partition(":")
        rules.append(ClassifyRule(name=name.strip(), pattern=pattern.strip()))
    return rules


def run_classify(args: argparse.Namespace) -> int:
    """Entry-point for the *classify* sub-command."""
    rules = _parse_rules(args.rules)
    opts = ClassifyOptions(
        rules=rules,
        default_category=args.default_category,
    )

    counts: Counter = Counter()
    try:
        for line, category in classify_lines(iter_lines(args.file), opts):
            counts[category] += 1
            if not args.summary:
                print(f"[{category}] {line.raw}")
    except FileNotFoundError:
        print(f"[logslice] File not found: {args.file}", file=sys.stderr)
        return 1

    if args.summary:
        print(f"{'Category':<24} {'Count':>8}")
        print("-" * 34)
        for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"{cat:<24} {count:>8}")

    return 0
