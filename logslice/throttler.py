"""Rate-based line throttling: emit at most N lines per time-window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class ThrottleOptions:
    """Configuration for rate-based throttling."""

    max_lines: int = 0          # maximum lines to emit per window
    window_seconds: float = 1.0 # rolling window size in seconds
    use_log_time: bool = True   # use log timestamp if available, else wall-clock

    def enabled(self) -> bool:
        return self.max_lines > 0 and self.window_seconds > 0


@dataclass
class _Window:
    """Sliding window state."""

    size: timedelta
    max_lines: int
    _timestamps: list = field(default_factory=list)

    def _evict(self, now: datetime) -> None:
        cutoff = now - self.size
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def allow(self, now: datetime) -> bool:
        self._evict(now)
        if len(self._timestamps) < self.max_lines:
            self._timestamps.append(now)
            return True
        return False


def _line_time(line: LogLine, wall: datetime) -> datetime:
    """Return the effective timestamp for throttle accounting."""
    return line.timestamp if line.timestamp is not None else wall


def throttle_lines(
    lines: Iterable[LogLine],
    opts: Optional[ThrottleOptions],
) -> Iterator[LogLine]:
    """Yield lines that fall within the allowed rate; drop excess lines."""
    if opts is None or not opts.enabled():
        yield from lines
        return

    window = _Window(
        size=timedelta(seconds=opts.window_seconds),
        max_lines=opts.max_lines,
    )

    for line in lines:
        now = _line_time(line, datetime.utcnow()) if opts.use_log_time else datetime.utcnow()
        if window.allow(now):
            yield line
