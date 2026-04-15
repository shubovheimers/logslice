"""Correlate log lines across sources by a shared request/trace ID."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Pattern

from logslice.parser import LogLine


@dataclass
class CorrelateOptions:
    """Options controlling log correlation."""

    field: str = "request_id"  # metadata key to correlate on
    pattern: Optional[str] = None  # regex to extract correlation id from raw text
    _compiled: Optional[Pattern[str]] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            self._compiled = re.compile(self.pattern)

    def enabled(self) -> bool:
        return bool(self.field or self.pattern)

    def extract_id(self, line: LogLine) -> Optional[str]:
        """Return the correlation ID for *line*, or None if not found."""
        if self._compiled:
            m = self._compiled.search(line.raw)
            if m:
                return m.group(1) if m.lastindex else m.group(0)
            return None
        return line.extra.get(self.field) if line.extra else None


def group_by_correlation(
    lines: Iterable[LogLine],
    opts: CorrelateOptions,
) -> Dict[str, List[LogLine]]:
    """Group *lines* by their correlation ID.

    Lines without a correlation ID are collected under the empty-string key.
    """
    groups: Dict[str, List[LogLine]] = {}
    for line in lines:
        cid = opts.extract_id(line) or ""
        groups.setdefault(cid, []).append(line)
    return groups


def iter_correlated(
    lines: Iterable[LogLine],
    opts: CorrelateOptions,
    target_id: str,
) -> Iterator[LogLine]:
    """Yield only lines whose correlation ID matches *target_id*."""
    for line in lines:
        if opts.extract_id(line) == target_id:
            yield line
