"""CLI helpers for the tracer feature."""
from __future__ import annotations

import argparse
from typing import Optional

from logslice.tracer import TraceOptions


def add_trace_args(parser: argparse.ArgumentParser) -> None:
    """Attach trace-related arguments to *parser*."""
    grp = parser.add_argument_group("tracing")
    grp.add_argument(
        "--trace-field",
        metavar="FIELD",
        default=None,
        help="Extra-field key that holds the trace/request ID.",
    )
    grp.add_argument(
        "--trace-pattern",
        metavar="REGEX",
        default=None,
        help="Regex with a named group 'trace_id' to extract from raw text.",
    )
    grp.add_argument(
        "--trace-id",
        metavar="ID",
        default=None,
        help="Only emit lines whose trace ID matches this value.",
    )


def trace_opts_from_args(args: argparse.Namespace) -> TraceOptions:
    """Build a :class:`TraceOptions` from parsed CLI arguments."""
    field: Optional[str] = getattr(args, "trace_field", None)
    pattern: Optional[str] = getattr(args, "trace_pattern", None)
    trace_id: Optional[str] = getattr(args, "trace_id", None)
    enabled = bool(field or pattern)
    return TraceOptions(
        enabled=enabled,
        field=field,
        pattern=pattern,
        trace_id=trace_id,
    )
