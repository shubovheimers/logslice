"""CLI helpers for the alerter feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.alerter import AlertOptions, AlertRule, AlertFired, evaluate_alerts
from logslice.reader import iter_lines


def add_alert_args(parser: argparse.ArgumentParser) -> None:
    """Attach alert-related arguments to *parser*."""
    parser.add_argument(
        "--alert",
        metavar="NAME:PATTERN:THRESHOLD:WINDOW",
        action="append",
        dest="alerts",
        default=[],
        help=(
            "Define an alert rule as NAME:PATTERN:THRESHOLD:WINDOW_SECONDS. "
            "May be repeated for multiple rules."
        ),
    )


def _parse_rules(raw: List[str]) -> List[AlertRule]:
    rules: List[AlertRule] = []
    for spec in raw:
        parts = spec.split(":", 3)
        if len(parts) < 2:
            raise argparse.ArgumentTypeError(
                f"Invalid alert spec {spec!r}. Expected NAME:PATTERN[:THRESHOLD[:WINDOW]]"
            )
        name = parts[0]
        pattern = parts[1]
        threshold = int(parts[2]) if len(parts) > 2 else 1
        window = int(parts[3]) if len(parts) > 3 else 60
        rules.append(AlertRule(name=name, pattern=pattern, threshold=threshold, window_seconds=window))
    return rules


def alert_opts_from_args(args: argparse.Namespace) -> AlertOptions:
    rules = _parse_rules(getattr(args, "alerts", []))
    return AlertOptions(rules=rules)


def run_alerts(args: argparse.Namespace) -> int:
    """Standalone entry-point: read *args.file*, print any fired alerts."""
    opts = alert_opts_from_args(args)
    if not opts.enabled:
        print("No alert rules defined.", file=sys.stderr)
        return 1

    fired_count = 0
    with iter_lines(args.file) as lines:
        for alert in evaluate_alerts(lines, opts):
            print(alert)
            fired_count += 1

    return 0 if fired_count else 0
