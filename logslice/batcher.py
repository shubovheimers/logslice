"""Batch log lines into fixed-size or time-windowed groups."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class BatchOptions:
    size: int = 0                        # max lines per batch (0 = disabled)
    window_seconds: float = 0.0          # max time span per batch in seconds

    def __post_init__(self) -> None:
        if self.size < 0:
            raise ValueError("size must be >= 0")
        if self.window_seconds < 0:
            raise ValueError("window_seconds must be >= 0")

    def enabled(self) -> bool:
        return self.size > 0 or self.window_seconds > 0.0


def _window(opts: BatchOptions) -> Optional[timedelta]:
    if opts.window_seconds > 0:
        return timedelta(seconds=opts.window_seconds)
    return None


def batch_lines(
    lines: Iterable[LogLine],
    opts: BatchOptions,
) -> Iterator[List[LogLine]]:
    """Yield lists of LogLine according to BatchOptions.

    Batches are flushed when:
    - the batch reaches *size* lines (if size > 0), or
    - the timestamp span within the batch exceeds *window_seconds* (if set).
    Either condition alone is sufficient to flush.
    """
    if not opts.enabled():
        # yield every line as its own single-item batch
        for line in lines:
            yield [line]
        return

    win = _window(opts)
    buf: List[LogLine] = []
    batch_start_ts = None

    for line in lines:
        if buf:
            # check time window
            if win is not None and line.timestamp is not None and batch_start_ts is not None:
                if line.timestamp - batch_start_ts >= win:
                    yield buf
                    buf = []
                    batch_start_ts = None

            # check size
            if opts.size > 0 and len(buf) >= opts.size:
                yield buf
                buf = []
                batch_start_ts = None

        if not buf and line.timestamp is not None:
            batch_start_ts = line.timestamp

        buf.append(line)

    if buf:
        yield buf
