"""stacker.py — accumulate log lines into fixed-size or time-bounded stacks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class StackOptions:
    max_lines: int = 0
    seconds: float = 0.0
    min_lines: int = 1

    def __post_init__(self) -> None:
        if self.max_lines < 0:
            raise ValueError("max_lines must be >= 0")
        if self.seconds < 0:
            raise ValueError("seconds must be >= 0")
        if self.min_lines < 1:
            raise ValueError("min_lines must be >= 1")

    @property
    def enabled(self) -> bool:
        return self.max_lines > 0 or self.seconds > 0.0


@dataclass
class Stack:
    lines: List[LogLine] = field(default_factory=list)
    index: int = 0

    def __len__(self) -> int:
        return len(self.lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Stack(index={self.index}, size={len(self.lines)})"


def _window_start(line: LogLine) -> Optional[datetime]:
    return line.timestamp


def stack_lines(
    lines: Iterator[LogLine],
    opts: StackOptions,
) -> Iterator[Stack]:
    """Yield Stack objects grouping lines by count or time window."""
    if not opts.enabled:
        yield from (Stack(lines=[ln], index=i) for i, ln in enumerate(lines))
        return

    bucket: List[LogLine] = []
    window_open: Optional[datetime] = None
    stack_index = 0
    deadline: Optional[datetime] = None

    for line in lines:
        if opts.seconds > 0.0:
            ts = _window_start(line)
            if window_open is None and ts is not None:
                window_open = ts
                deadline = ts + timedelta(seconds=opts.seconds)

            if deadline is not None and ts is not None and ts >= deadline:
                if len(bucket) >= opts.min_lines:
                    yield Stack(lines=list(bucket), index=stack_index)
                    stack_index += 1
                bucket = []
                window_open = ts
                deadline = ts + timedelta(seconds=opts.seconds)

        bucket.append(line)

        if opts.max_lines > 0 and len(bucket) >= opts.max_lines:
            if len(bucket) >= opts.min_lines:
                yield Stack(lines=list(bucket), index=stack_index)
                stack_index += 1
            bucket = []
            window_open = None
            deadline = None

    if bucket and len(bucket) >= opts.min_lines:
        yield Stack(lines=list(bucket), index=stack_index)
