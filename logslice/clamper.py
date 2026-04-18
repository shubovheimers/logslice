"""Clamper: restrict log line timestamps to a bounded range."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class ClampOptions:
    enabled: bool = False
    floor: Optional[datetime] = None
    ceiling: Optional[datetime] = None
    replace_with_bound: bool = True  # False => drop out-of-range lines

    def __post_init__(self) -> None:
        if self.floor and self.ceiling and self.floor > self.ceiling:
            raise ValueError("floor must not be later than ceiling")

    def is_active(self) -> bool:
        return self.enabled and (self.floor is not None or self.ceiling is not None)


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _clamp_ts(ts: datetime, floor: Optional[datetime], ceiling: Optional[datetime]) -> datetime:
    if floor and ts < _utc(floor):
        return _utc(floor)
    if ceiling and ts > _utc(ceiling):
        return _utc(ceiling)
    return ts


def clamp_lines(
    lines: Iterable[LogLine],
    opts: Optional[ClampOptions],
) -> Iterator[LogLine]:
    if opts is None or not opts.is_active():
        yield from lines
        return

    floor = _utc(opts.floor) if opts.floor else None
    ceiling = _utc(opts.ceiling) if opts.ceiling else None

    for line in lines:
        if line.timestamp is None:
            yield line
            continue

        ts = _utc(line.timestamp)

        below_floor = floor and ts < floor
        above_ceiling = ceiling and ts > ceiling

        if below_floor or above_ceiling:
            if not opts.replace_with_bound:
                continue
            clamped = _clamp_ts(ts, floor, ceiling)
            yield LogLine(
                raw=line.raw,
                timestamp=clamped,
                level=line.level,
                message=line.message,
                extra=line.extra,
            )
        else:
            yield line
