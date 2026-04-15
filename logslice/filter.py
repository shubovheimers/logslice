"""Filter log lines by time range, log level, or pattern."""

import re
from datetime import datetime
from typing import Iterator, Optional, List

from logslice.parser import LogLine

LEVEL_PRIORITY = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "WARN": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "FATAL": 50,
}


def filter_by_time(
    lines: Iterator[LogLine],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Iterator[LogLine]:
    """Yield log lines whose timestamp falls within [start, end].

    Lines without a parsed timestamp are skipped.
    """
    if start and end and start > end:
        raise ValueError(
            f"start ({start!r}) must not be later than end ({end!r})"
        )
    for line in lines:
        if line.timestamp is None:
            continue
        if start and line.timestamp < start:
            continue
        if end and line.timestamp > end:
            continue
        yield line


def filter_by_level(
    lines: Iterator[LogLine],
    min_level: str,
) -> Iterator[LogLine]:
    """Yield log lines at or above the given minimum log level."""
    min_priority = LEVEL_PRIORITY.get(min_level.upper())
    if min_priority is None:
        raise ValueError(
            f"Unknown log level: {min_level!r}. "
            f"Valid levels: {list(LEVEL_PRIORITY.keys())}"
        )
    for line in lines:
        if line.level is None:
            continue
        priority = LEVEL_PRIORITY.get(line.level.upper(), 0)
        if priority >= min_priority:
            yield line


def filter_by_pattern(
    lines: Iterator[LogLine],
    pattern: str,
    flags: int = re.IGNORECASE,
) -> Iterator[LogLine]:
    """Yield log lines whose raw text matches the given regex pattern."""
    compiled = re.compile(pattern, flags)
    for line in lines:
        if compiled.search(line.raw):
            yield line


def apply_filters(
    lines: Iterator[LogLine],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_level: Optional[str] = None,
    pattern: Optional[str] = None,
) -> Iterator[LogLine]:
    """Apply all active filters in sequence."""
    if start or end:
        lines = filter_by_time(lines, start=start, end=end)
    if min_level:
        lines = filter_by_level(lines, min_level)
    if pattern:
        lines = filter_by_pattern(lines, pattern)
    return lines
