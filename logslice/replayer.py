"""Replay log lines with timing delays proportional to original timestamps."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class ReplayOptions:
    enabled: bool = False
    speed: float = 1.0          # multiplier: 2.0 = twice as fast, 0.5 = half speed
    max_delay: float = 5.0      # seconds — cap between-line waits
    real_time: bool = False     # if True, ignore speed and use actual elapsed time

    def __post_init__(self) -> None:
        if self.speed <= 0:
            raise ValueError("speed must be greater than zero")
        if self.max_delay < 0:
            raise ValueError("max_delay must be non-negative")


def _delta_seconds(prev: datetime, curr: datetime) -> float:
    """Return non-negative seconds between two timestamps."""
    delta: timedelta = curr - prev
    return max(delta.total_seconds(), 0.0)


def replay_lines(
    lines: Iterable[LogLine],
    opts: Optional[ReplayOptions] = None,
    *,
    _sleep=time.sleep,
) -> Iterator[LogLine]:
    """Yield lines, sleeping between them to simulate original timing.

    Lines without timestamps are yielded immediately.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    prev_ts: Optional[datetime] = None

    for line in lines:
        if line.timestamp is not None and prev_ts is not None:
            raw_gap = _delta_seconds(prev_ts, line.timestamp)
            if opts.real_time:
                delay = min(raw_gap, opts.max_delay)
            else:
                delay = min(raw_gap / opts.speed, opts.max_delay)
            if delay > 0:
                _sleep(delay)

        if line.timestamp is not None:
            prev_ts = line.timestamp

        yield line
