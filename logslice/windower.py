"""Sliding/tumbling window aggregation over log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class WindowOptions:
    enabled: bool = False
    size_seconds: int = 60
    step_seconds: Optional[int] = None  # None => tumbling; set => sliding
    min_lines: int = 1

    def __post_init__(self) -> None:
        if self.size_seconds <= 0:
            raise ValueError("size_seconds must be positive")
        if self.step_seconds is not None and self.step_seconds <= 0:
            raise ValueError("step_seconds must be positive")

    @property
    def is_sliding(self) -> bool:
        return self.step_seconds is not None


@dataclass
class Window:
    start: datetime
    end: datetime
    lines: List[LogLine] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.lines)


def window_lines(lines: Iterator[LogLine], opts: WindowOptions) -> Iterator[Window]:
    """Yield Window objects over timestamped log lines."""
    if not opts.enabled:
        return

    size = timedelta(seconds=opts.size_seconds)
    step = timedelta(seconds=opts.step_seconds) if opts.is_sliding else size

    buf: List[LogLine] = []
    for line in lines:
        if line.timestamp is not None:
            buf.append(line)

    if not buf:
        return

    first_ts = buf[0].timestamp
    win_start = first_ts

    while True:
        win_end = win_start + size
        window = Window(start=win_start, end=win_end)
        for ln in buf:
            if win_start <= ln.timestamp < win_end:  # type: ignore[operator]
                window.lines.append(ln)
        if len(window) >= opts.min_lines:
            yield window
        win_start += step
        if win_start >= buf[-1].timestamp:  # type: ignore[operator]
            break
