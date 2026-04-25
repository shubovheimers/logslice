"""Time-boundary clamping for log line timestamps.

Clamps log line timestamps to a configurable [floor, ceiling] window,
optionally replacing out-of-range timestamps with the nearest boundary
or dropping lines that fall outside the window entirely.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class ClampTimeOptions:
    floor: Optional[datetime] = None
    ceiling: Optional[datetime] = None
    drop_out_of_range: bool = False
    replace_with_boundary: bool = True

    def __post_init__(self) -> None:
        if self.floor is not None and self.ceiling is not None:
            if self.floor > self.ceiling:
                raise ValueError(
                    f"floor ({self.floor}) must not be later than ceiling ({self.ceiling})"
                )

    @property
    def is_active(self) -> bool:
        return self.floor is not None or self.ceiling is not None


def _utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware for comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clamp_time_lines(
    lines: Iterable[LogLine],
    opts: Optional[ClampTimeOptions],
) -> Iterator[LogLine]:
    """Yield lines with timestamps clamped to [floor, ceiling].

    If *drop_out_of_range* is True, lines whose timestamps fall outside
    the window are silently dropped.  Otherwise, when *replace_with_boundary*
    is True (the default) the timestamp is replaced with the nearest boundary;
    if both flags are False the line is yielded unchanged.
    """
    if opts is None or not opts.is_active:
        yield from lines
        return

    floor = _utc(opts.floor) if opts.floor is not None else None
    ceiling = _utc(opts.ceiling) if opts.ceiling is not None else None

    for line in lines:
        if line.timestamp is None:
            yield line
            continue

        ts = _utc(line.timestamp)

        if floor is not None and ts < floor:
            if opts.drop_out_of_range:
                continue
            if opts.replace_with_boundary:
                line = LogLine(
                    raw=line.raw,
                    timestamp=opts.floor,
                    level=line.level,
                    message=line.message,
                    extra=line.extra,
                )
        elif ceiling is not None and ts > ceiling:
            if opts.drop_out_of_range:
                continue
            if opts.replace_with_boundary:
                line = LogLine(
                    raw=line.raw,
                    timestamp=opts.ceiling,
                    level=line.level,
                    message=line.message,
                    extra=line.extra,
                )

        yield line
