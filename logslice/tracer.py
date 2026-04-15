"""Request/trace-ID tracing: extract and follow a trace ID across log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class TraceOptions:
    enabled: bool = False
    field: Optional[str] = None          # extra-field key to read trace id from
    pattern: Optional[str] = None        # regex with a named group 'trace_id'
    trace_id: Optional[str] = None       # the specific id to follow (None = collect all)
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            self._compiled = re.compile(self.pattern)

    def is_active(self) -> bool:
        return self.enabled and (self.field is not None or self._compiled is not None)


def extract_trace_id(line: LogLine, opts: TraceOptions) -> Optional[str]:
    """Return the trace ID found in *line*, or None."""
    if opts.field and opts.field in (line.extra or {}):
        return str(line.extra[opts.field])
    if opts._compiled:
        m = opts._compiled.search(line.raw)
        if m:
            try:
                return m.group("trace_id")
            except IndexError:
                return m.group(0)
    return None


def group_by_trace(
    lines: Iterable[LogLine],
    opts: TraceOptions,
) -> dict[str, list[LogLine]]:
    """Collect lines into buckets keyed by trace ID."""
    buckets: dict[str, list[LogLine]] = {}
    for line in lines:
        tid = extract_trace_id(line, opts)
        if tid is None:
            continue
        buckets.setdefault(tid, []).append(line)
    return buckets


def trace_lines(
    lines: Iterable[LogLine],
    opts: TraceOptions,
) -> Iterator[LogLine]:
    """Yield only lines that carry the requested trace ID (or all traced lines)."""
    if not opts.is_active():
        yield from lines
        return
    for line in lines:
        tid = extract_trace_id(line, opts)
        if tid is None:
            continue
        if opts.trace_id is None or tid == opts.trace_id:
            yield line
