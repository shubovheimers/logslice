"""Log sampling utilities for reducing output volume."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class SampleOptions:
    """Configuration for log sampling."""

    every_nth: int = 1          # keep every N-th line (1 = keep all)
    max_lines: Optional[int] = None  # hard cap on total output lines
    head: Optional[int] = None  # keep only first N lines
    tail: Optional[int] = None  # keep only last N lines


def sample_every_nth(lines: Iterable[LogLine], n: int) -> Iterator[LogLine]:
    """Yield every n-th log line (1-indexed)."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for i, line in enumerate(lines):
        if i % n == 0:
            yield line


def sample_head(lines: Iterable[LogLine], count: int) -> Iterator[LogLine]:
    """Yield at most the first *count* lines."""
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    for i, line in enumerate(lines):
        if i >= count:
            break
        yield line


def sample_tail(lines: Iterable[LogLine], count: int) -> Iterator[LogLine]:
    """Yield only the last *count* lines (buffers in memory)."""
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    from collections import deque
    buf: deque[LogLine] = deque(maxlen=count)
    for line in lines:
        buf.append(line)
    yield from buf


def apply_sampling(lines: Iterable[LogLine], opts: SampleOptions) -> Iterator[LogLine]:
    """Apply all sampling options in order: tail → every_nth → head → max_lines."""
    stream: Iterable[LogLine] = lines

    if opts.tail is not None:
        stream = sample_tail(stream, opts.tail)

    if opts.every_nth != 1:
        stream = sample_every_nth(stream, opts.every_nth)

    if opts.head is not None:
        stream = sample_head(stream, opts.head)

    if opts.max_lines is not None:
        stream = sample_head(stream, opts.max_lines)

    yield from stream
