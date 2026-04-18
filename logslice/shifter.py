"""Timestamp shifting — offset all log line timestamps by a fixed delta."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class ShiftOptions:
    seconds: float = 0.0
    minutes: float = 0.0
    hours: float = 0.0
    days: float = 0.0
    # pre-built delta (takes precedence when set internally)
    _delta: Optional[timedelta] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._delta = timedelta(
            seconds=self.seconds,
            minutes=self.minutes,
            hours=self.hours,
            days=self.days,
        )

    @property
    def enabled(self) -> bool:
        return self._delta is not None and self._delta != timedelta(0)

    @property
    def delta(self) -> timedelta:
        assert self._delta is not None
        return self._delta


def _shift_timestamp(ts: Optional[datetime], delta: timedelta) -> Optional[datetime]:
    if ts is None:
        return None
    return ts + delta


def shift_lines(
    lines: Iterable[LogLine],
    opts: Optional[ShiftOptions],
) -> Iterator[LogLine]:
    """Yield lines with timestamps shifted by *opts.delta*.

    Lines without a timestamp are passed through unchanged.
    When *opts* is None or disabled every line is yielded as-is.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    delta = opts.delta
    for line in lines:
        if line.timestamp is None:
            yield line
        else:
            yield LogLine(
                raw=line.raw,
                timestamp=_shift_timestamp(line.timestamp, delta),
                level=line.level,
                message=line.message,
                extra=line.extra,
            )
