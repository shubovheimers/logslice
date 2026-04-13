"""Merge multiple log streams into a single time-ordered sequence."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class MergeOptions:
    """Configuration for log stream merging."""

    tag_source: bool = False  # prepend source label to raw text
    stable: bool = True       # preserve insertion order for equal timestamps


def _sort_key(tagged: tuple) -> tuple:
    """Return a sort key for a tagged (ts_or_none, counter, label, line) tuple."""
    ts, counter, _label, _line = tagged
    # Lines without a timestamp sort after all timestamped lines
    return (ts is None, ts, counter)


def merge_logs(
    sources: List[tuple[str, Iterable[LogLine]]],
    opts: Optional[MergeOptions] = None,
) -> Iterator[LogLine]:
    """Merge named log sources into a single time-ordered iterator.

    Args:
        sources: List of (label, iterable_of_LogLine) pairs.
        opts:    Merge options; uses defaults when None.

    Yields:
        LogLine objects in ascending timestamp order.
    """
    if opts is None:
        opts = MergeOptions()

    # Build a min-heap seeded with the first item from each source.
    heap: list = []
    iters = [(label, iter(it)) for label, it in sources]
    counter = 0

    for label, it in iters:
        line = next(it, None)
        if line is not None:
            ts = line.timestamp
            heapq.heappush(heap, (ts is None, ts, counter, label, line, it))
            counter += 1

    while heap:
        _none_first, _ts, _cnt, label, line, it = heapq.heappop(heap)

        if opts.tag_source:
            tagged_raw = f"[{label}] {line.raw}"
            line = LogLine(
                raw=tagged_raw,
                timestamp=line.timestamp,
                level=line.level,
                message=line.message,
            )

        yield line

        nxt = next(it, None)
        if nxt is not None:
            ts = nxt.timestamp
            heapq.heappush(heap, (ts is None, ts, counter, label, nxt, it))
            counter += 1
