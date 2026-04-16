"""Sort log lines by timestamp or level."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine

LEVEL_ORDER = {
    "debug": 0,
    "info": 1,
    "notice": 2,
    "warning": 3,
    "warn": 3,
    "error": 4,
    "critical": 5,
    "fatal": 5,
}


@dataclass
class SortOptions:
    by: str = "timestamp"  # "timestamp" | "level" | "lineno"
    reverse: bool = False
    stable: bool = True
    buffer_size: Optional[int] = None  # None = unbounded (full sort)

    def __post_init__(self) -> None:
        valid = {"timestamp", "level", "lineno"}
        if self.by not in valid:
            raise ValueError(f"sort 'by' must be one of {valid}, got {self.by!r}")

    def enabled(self) -> bool:
        return True


def _sort_key(opts: SortOptions):
    def key(line: LogLine):
        if opts.by == "timestamp":
            return (line.timestamp is None, line.timestamp)
        if opts.by == "level":
            lvl = (line.level or "").lower()
            return LEVEL_ORDER.get(lvl, -1)
        # lineno
        return line.lineno
    return key


def sort_lines(
    lines: Iterable[LogLine],
    opts: Optional[SortOptions] = None,
) -> Iterator[LogLine]:
    """Buffer and sort lines according to *opts*."""
    if opts is None:
        yield from lines
        return

    key = _sort_key(opts)

    if opts.buffer_size is None:
        yield from sorted(lines, key=key, reverse=opts.reverse)
        return

    # Windowed / chunked sort
    buf: list[LogLine] = []
    for line in lines:
        buf.append(line)
        if len(buf) >= opts.buffer_size:
            yield from sorted(buf, key=key, reverse=opts.reverse)
            buf.clear()
    if buf:
        yield from sorted(buf, key=key, reverse=opts.reverse)
