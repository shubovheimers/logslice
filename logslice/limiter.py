"""Rate-limit log lines by capping output to N lines per time bucket."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class LimitOptions:
    max_lines: int = 0          # max lines allowed per window; 0 = disabled
    window_seconds: int = 1     # rolling window size in seconds

    def __post_init__(self) -> None:
        if self.max_lines < 0:
            raise ValueError("max_lines must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    @property
    def enabled(self) -> bool:
        return self.max_lines > 0


@dataclass
class _Window:
    start: datetime
    count: int = 0


def limit_lines(
    lines: Iterable[LogLine],
    opts: Optional[LimitOptions],
) -> Iterator[LogLine]:
    """Yield at most *max_lines* per *window_seconds* rolling window.

    Lines without a timestamp are always passed through.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    window: Optional[_Window] = None
    delta = timedelta(seconds=opts.window_seconds)

    for line in lines:
        if line.timestamp is None:
            yield line
            continue

        ts = line.timestamp
        if window is None or ts >= window.start + delta:
            window = _Window(start=ts)

        if window.count < opts.max_lines:
            window.count += 1
            yield line
        # else: drop the line silently
