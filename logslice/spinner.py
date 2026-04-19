"""spinner.py – rotate/cycle through a fixed-size sliding window of log lines.

SpinOptions controls the window size and step; spin_lines yields Window-like
objects containing consecutive slices of the input stream.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List

from logslice.parser import LogLine


@dataclass
class SpinOptions:
    size: int = 0          # number of lines per window; 0 = disabled
    step: int = 1          # how many lines to advance between windows
    partial: bool = False  # emit trailing windows smaller than size

    def __post_init__(self) -> None:
        if self.size < 0:
            raise ValueError("SpinOptions.size must be >= 0")
        if self.step < 1:
            raise ValueError("SpinOptions.step must be >= 1")

    @property
    def enabled(self) -> bool:
        return self.size > 0


@dataclass
class SpinWindow:
    lines: List[LogLine] = field(default_factory=list)
    index: int = 0          # zero-based window sequence number

    def __len__(self) -> int:
        return len(self.lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SpinWindow(index={self.index}, lines={len(self.lines)})"


def spin_lines(
    source: Iterable[LogLine],
    opts: SpinOptions,
) -> Iterator[SpinWindow]:
    """Yield SpinWindow objects over *source* according to *opts*.

    If opts is not enabled, yields a single window containing all lines.
    """
    if not opts.enabled:
        yield SpinWindow(lines=list(source), index=0)
        return

    buf: deque[LogLine] = deque(maxlen=opts.size)
    pending: int = 0          # lines until next emit
    window_index: int = 0

    for line in source:
        buf.append(line)
        if len(buf) == opts.size and pending == 0:
            yield SpinWindow(lines=list(buf), index=window_index)
            window_index += 1
            pending = opts.step
        if pending > 0:
            pending -= 1

    if opts.partial and buf:
        # emit whatever is left if it hasn't already been emitted
        last = list(buf)
        yield SpinWindow(lines=last, index=window_index)
