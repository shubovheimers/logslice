"""Seekable log reader that uses a LogIndex to skip to a time range."""

from __future__ import annotations

import gzip
from datetime import datetime
from typing import Generator, Optional

from logslice.indexer import LogIndex, build_index
from logslice.parser import LogLine, parse_line


def _open_binary(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rb")
    return open(path, "rb")


def iter_from_offset(
    path: str,
    offset: int,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Generator[LogLine, None, None]:
    """Yield parsed LogLines starting from *offset*, optionally bounded by time."""
    with _open_binary(path) as fh:  # type: ignore[call-overload]
        fh.seek(offset)
        for raw in fh:
            line = parse_line(raw.decode("utf-8", errors="replace"))
            if start and line.timestamp and line.timestamp < start:
                continue
            if end and line.timestamp and line.timestamp > end:
                break
            yield line


def seek_and_iter(
    path: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    index: Optional[LogIndex] = None,
    sample_every: int = 100,
) -> Generator[LogLine, None, None]:
    """Seek to the nearest indexed position before *start* and iterate.

    If no index is provided one is built on-the-fly (not cached).
    Falls back to offset 0 when no start time is given.
    """
    if index is None:
        index = build_index(path, sample_every=sample_every)

    offset = 0
    if start is not None and index.entries:
        offset = index.find_offset(start)

    yield from iter_from_offset(path, offset=offset, start=start, end=end)
