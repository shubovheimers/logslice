"""Time-based log splitting utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, List

from logslice.parser import LogLine


@dataclass
class TimeSlice:
    """A contiguous slice of log lines within a time window."""

    start: datetime
    end: datetime
    lines: List[LogLine] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TimeSlice({self.start} -> {self.end}, lines={len(self.lines)})"


@dataclass
class TimeSliceOptions:
    window_seconds: int = 3600
    drop_empty: bool = True

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")


def slice_by_time(
    lines: Iterator[LogLine],
    opts: TimeSliceOptions,
) -> Iterator[TimeSlice]:
    """Yield TimeSlice objects grouping lines into fixed time windows."""
    window = timedelta(seconds=opts.window_seconds)
    current_start: datetime | None = None
    current_end: datetime | None = None
    bucket: List[LogLine] = []

    for line in lines:
        ts = line.timestamp
        if ts is None:
            if bucket:
                bucket.append(line)
            continue

        if current_start is None:
            current_start = ts
            current_end = ts + window

        if ts >= current_end:
            if bucket or not opts.drop_empty:
                yield TimeSlice(start=current_start, end=current_end, lines=bucket)
            # Advance window(s)
            while ts >= current_end:
                current_start = current_end
                current_end = current_start + window
            bucket = []

        bucket.append(line)

    if current_start is not None and (bucket or not opts.drop_empty):
        yield TimeSlice(start=current_start, end=current_end, lines=bucket)
